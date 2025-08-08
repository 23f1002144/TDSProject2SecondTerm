import openai
import os
import json
import re
from typing import Dict, Any, List, Optional
import logging
import pandas as pd
import asyncio

logger = logging.getLogger(__name__)


class LLMAnalyzer:
    """Uses OpenAI LLM to analyze questions and generate appropriate analysis code (OPENAI_API_KEY only)."""

    def __init__(self):
        # Reverted: only OPENAI_API_KEY is supported now
        api_key = os.getenv("OPENAI_API_KEY")
        self.client = openai.AsyncOpenAI(api_key=api_key) if api_key else None
        if not api_key:
            logger.warning(
                "OPENAI_API_KEY not set. LLM analysis will not work (will use heuristics only)."
            )
        # Fixed model name
        self.model = "gpt-4"

    async def create_analysis_plan(
        self, questions_content: str, data_files: Dict[str, str]
    ) -> Dict[str, Any]:
        """
        Analyze the questions and create an execution plan.

        Args:
            questions_content: Content of questions.txt
            data_files: Dictionary of available data files

        Returns:
            Analysis plan with structured questions and required operations
        """
        try:
            parsed_questions = await self._parse_questions(questions_content)

            plan = {
                "questions": parsed_questions,
                "data_files": list(data_files.keys()),
                "analysis_types": [q.get("type") for q in parsed_questions],
            }

            return plan

        except Exception as e:
            logger.error(f"Error creating analysis plan: {str(e)}")
            return {"error": str(e), "questions": []}

    async def _parse_questions(self, questions_content: str) -> List[Dict[str, Any]]:
        """Parse questions and classify analysis types."""
        # If no client (no key), use fallback immediately
        if not self.client:  # fallback if no key
            return self._basic_question_parsing(questions_content)
        try:
            system_prompt = (
                "You are a data analysis expert. Parse the given questions and classify each question by its analysis type.\n"
                "Analysis types: web_scraping, data_analysis, statistical, visualization, general.\n"
                "Return ONLY a JSON array with objects: {text, type, url, output_format, requires_visualization}."
            )

            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {
                        "role": "user",
                        "content": f"Questions to analyze:\n\n{questions_content}",
                    },
                ],
                temperature=0.1,
            )
            result = response.choices[0].message.content
            json_match = re.search(r"\[.*\]", result, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            return self._basic_question_parsing(questions_content)
        except Exception as e:
            logger.error(f"Error parsing questions with LLM: {str(e)}")
            return self._basic_question_parsing(questions_content)

    def _basic_question_parsing(self, questions_content: str) -> List[Dict[str, Any]]:
        """Fallback question parsing without LLM."""
        questions = []
        parts = re.split(r"\n\s*\d+\.", questions_content)
        for part in parts:
            if not part.strip():
                continue
            lower = part.lower()
            qtype = "general"
            if "scrape" in lower or "http" in lower or "wikipedia" in lower:
                qtype = "web_scraping"
            elif any(k in lower for k in ["plot", "chart", "scatter"]):
                qtype = "visualization"
            elif any(k in lower for k in ["correlation", "regression", "slope"]):
                qtype = "statistical"
            elif "data" in lower:
                qtype = "data_analysis"
            url_match = re.search(r"https?://[^\s]+", part)
            questions.append(
                {
                    "text": part.strip(),
                    "type": qtype,
                    "url": url_match.group() if url_match else None,
                    "output_format": "json",
                    "requires_visualization": any(
                        k in lower for k in ["plot", "chart", "scatter"]
                    ),
                }
            )
        return questions

    async def analyze_data(
        self, question: Dict[str, Any], data: Dict[str, pd.DataFrame]
    ) -> Any:
        """
        Analyze data using LLM to generate and execute Python code.

        Args:
            question: Question details
            data: Dictionary of dataframes

        Returns:
            Analysis result
        """
        if not self.client:
            return "LLM unavailable (OPENAI_API_KEY missing)."
        try:
            data_description = "".join(
                f"\n{name}: {df.shape} - Columns: {list(df.columns)}"
                for name, df in data.items()
            )
            system_prompt = (
                "You are a data analyst. Generate Python code to answer the question using the provided data.\n"
                f"Available data:{data_description}\n"
                "Rules:\n1. Use only pandas, numpy, scipy (stats) and stdlib\n2. DataFrames available by filename without extension\n3. Assign final answer to variable 'result'\n4. Be concise."
            )
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Question: {question['text']}"},
                ],
                temperature=0.05,
            )
            code = response.choices[0].message.content
            return await self._execute_analysis_code(code, data)
        except Exception as e:
            logger.error(f"Error in LLM data analysis: {e}")
            return f"Error: {e}"

    async def _execute_analysis_code(
        self, code: str, data: Dict[str, pd.DataFrame]
    ) -> Any:
        """Execute generated analysis code safely."""
        try:
            lines, in_block = [], False
            for line in code.split("\n"):
                if line.strip().startswith("```python"):
                    in_block = True
                    continue
                if line.strip().startswith("```") and in_block:
                    in_block = False
                    continue
                if in_block or not line.strip().startswith("```"):
                    lines.append(line)
            clean_code = "\n".join(lines)
            exec_globals = {
                "pd": pd,
                "np": __import__("numpy"),
                "stats": __import__("scipy.stats", fromlist=["stats"]).stats,
            }
            for filename, df in data.items():
                var = os.path.splitext(filename)[0].replace("-", "_").replace(" ", "_")
                exec_globals[var] = df
                exec_globals["df"] = df
            exec_locals: Dict[str, Any] = {}
            exec(clean_code, exec_globals, exec_locals)
            if "result" in exec_locals:
                return exec_locals["result"]
            if "answer" in exec_locals:
                return exec_locals["answer"]
            return list(exec_locals.values())[-1] if exec_locals else None
        except Exception as e:
            logger.error(f"Error executing analysis code: {e}")
            return f"Execution error: {e}"

    async def format_results(
        self, questions_content: str, results: Dict[str, Any]
    ) -> Any:
        """
        Format analysis results according to the expected output format.

        Args:
            questions_content: Original questions
            results: Analysis results

        Returns:
            Formatted results (JSON array, object, etc.)
        """
        try:
            # Determine expected output format from questions
            if "JSON array" in questions_content or "json array" in questions_content:
                # Return as array
                result_values = []
                for key in sorted(results.keys()):
                    result_values.append(results[key])
                return result_values

            elif (
                "JSON object" in questions_content or "json object" in questions_content
            ):
                # Return as object - extract answers from questions
                formatted_results = {}

                # Try to match questions to results
                question_lines = [
                    line.strip()
                    for line in questions_content.split("\n")
                    if line.strip() and any(char in line for char in ["?", ":"])
                ]

                for i, line in enumerate(question_lines, 1):
                    key = line.split(":")[0].strip() if ":" in line else line
                    rk = f"question_{i}"
                    if rk in results:
                        formatted_results[key] = results[rk]

                return formatted_results

            else:
                # Default: return as array
                result_values = []
                for key in sorted(results.keys()):
                    result_values.append(results[key])
                return result_values

        except Exception as e:
            logger.error(f"Error formatting results: {e}")
            return results

    async def general_analysis(
        self, question: Dict[str, Any], data_files: Dict[str, str]
    ) -> Any:
        """
        Handle general analysis tasks using LLM.

        Args:
            question: Question details
            data_files: Available data files

        Returns:
            Analysis result
        """
        if not self.client:
            return "LLM unavailable (OPENAI_API_KEY missing)."
        try:
            system_prompt = "You are a data analysis expert. Provide a concise answer."
            context = f"Question: {question['text']}\nAvailable files: {list(data_files.keys())}"
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": context},
                ],
                temperature=0.3,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"Error in general analysis: {e}")
            return f"Error: {e}"
