from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import os
import json
import tempfile
from typing import List, Dict, Any, Optional
import asyncio
import logging
from datetime import datetime

from services.data_processor import DataProcessor
from services.llm_analyzer import LLMAnalyzer
from services.visualization_engine import VisualizationEngine
from utils.file_handler import FileHandler

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Data Analyst Agent API",
    description="An API that uses LLMs to source, prepare, analyze, and visualize data",
    version="1.0.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
data_processor = DataProcessor()
llm_analyzer = LLMAnalyzer()
visualization_engine = VisualizationEngine()
file_handler = FileHandler()


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Data Analyst Agent API",
        "version": "1.0.0",
        "endpoints": {"analysis": "/api/", "health": "/health"},
        "timestamp": datetime.now().isoformat(),
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


@app.post("/api/")
async def analyze_data(files: List[UploadFile] = File(...)):
    """
    Main analysis endpoint that accepts questions and optional data files.
    """
    try:
        logger.info(f"Received {len(files)} files for analysis")

        # Process uploaded files
        questions_content = None
        data_files = {}

        for file in files:
            if (
                file.filename.endswith("questions.txt")
                or file.filename == "questions.txt"
            ):
                content = await file.read()
                questions_content = content.decode("utf-8")
                logger.info(f"Questions loaded: {len(questions_content)} characters")
            else:
                # Store other files for data processing
                content = await file.read()
                data_files[file.filename] = {
                    "content": content,
                    "content_type": file.content_type,
                }
                logger.info(f"Data file loaded: {file.filename}")

        if not questions_content:
            raise HTTPException(
                status_code=400, detail="questions.txt file is required"
            )

        # Create temporary directory for file processing
        with tempfile.TemporaryDirectory() as temp_dir:
            # Save files to temporary directory
            saved_files = await file_handler.save_files(data_files, temp_dir)

            # Analyze the questions using LLM
            analysis_plan = await llm_analyzer.create_analysis_plan(
                questions_content, saved_files
            )
            logger.info(
                f"Analysis plan created: {len(analysis_plan.get('steps', []))} steps"
            )

            # Execute the analysis
            results = await execute_analysis(analysis_plan, saved_files, temp_dir)

            # Format results according to the questions
            formatted_results = await llm_analyzer.format_results(
                questions_content, results
            )

            logger.info("Analysis completed successfully")
            return JSONResponse(content=formatted_results)

    except Exception as e:
        logger.error(f"Error in analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


async def execute_analysis(
    analysis_plan: Dict[str, Any], data_files: Dict[str, str], temp_dir: str
):
    """Execute the analysis plan step by step."""
    results = {}

    try:
        # Extract questions from the plan
        questions = analysis_plan.get("questions", [])

        for i, question in enumerate(questions):
            logger.info(
                f"Processing question {i+1}: {question.get('text', '')[:100]}..."
            )

            # Determine the type of analysis needed
            analysis_type = question.get("type", "general")

            if analysis_type == "web_scraping":
                result = await handle_web_scraping(question, temp_dir)
            elif analysis_type == "data_analysis":
                result = await handle_data_analysis(question, data_files, temp_dir)
            elif analysis_type == "visualization":
                result = await handle_visualization(question, data_files, temp_dir)
            elif analysis_type == "statistical":
                result = await handle_statistical_analysis(
                    question, data_files, temp_dir
                )
            else:
                result = await handle_general_analysis(question, data_files, temp_dir)

            results[f"question_{i+1}"] = result

    except Exception as e:
        logger.error(f"Error executing analysis: {str(e)}")
        raise

    return results


async def handle_web_scraping(question: Dict[str, Any], temp_dir: str):
    """Handle web scraping tasks."""
    url = question.get("url")
    if url:
        return await data_processor.scrape_web_data(url)
    return None


async def handle_data_analysis(
    question: Dict[str, Any], data_files: Dict[str, str], temp_dir: str
):
    """Handle general data analysis tasks."""
    # Process data files
    processed_data = {}
    for filename, filepath in data_files.items():
        if filename.endswith((".csv", ".json", ".xlsx", ".parquet")):
            processed_data[filename] = await data_processor.load_data(filepath)

    # Perform analysis using LLM
    return await llm_analyzer.analyze_data(question, processed_data)


async def handle_visualization(
    question: Dict[str, Any], data_files: Dict[str, str], temp_dir: str
):
    """Handle visualization tasks."""
    # Load and process data
    data = None
    for filename, filepath in data_files.items():
        if filename.endswith((".csv", ".json", ".xlsx")):
            data = await data_processor.load_data(filepath)
            break

    if data is not None:
        return await visualization_engine.create_visualization(question, data, temp_dir)
    return None


async def handle_statistical_analysis(
    question: Dict[str, Any], data_files: Dict[str, str], temp_dir: str
):
    """Handle statistical analysis tasks."""
    # Load data
    data = None
    for filename, filepath in data_files.items():
        if filename.endswith((".csv", ".json", ".xlsx")):
            data = await data_processor.load_data(filepath)
            break

    if data is not None:
        return await data_processor.statistical_analysis(question, data)
    return None


async def handle_general_analysis(
    question: Dict[str, Any], data_files: Dict[str, str], temp_dir: str
):
    """Handle general analysis tasks using LLM."""
    return await llm_analyzer.general_analysis(question, data_files)


if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
