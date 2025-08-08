import pandas as pd
import numpy as np
import requests
from bs4 import BeautifulSoup
import json
import os
from typing import Dict, Any, Optional, List
import logging
from scipy import stats
import duckdb
import asyncio

logger = logging.getLogger(__name__)


class DataProcessor:
    """Handles data sourcing, preparation, and basic analysis."""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
            }
        )

    async def scrape_web_data(self, url: str) -> Dict[str, Any]:
        """
        Scrape data from web pages.

        Args:
            url: URL to scrape

        Returns:
            Dictionary containing scraped data
        """
        try:
            logger.info(f"Scraping data from: {url}")

            # Handle specific sites
            if "wikipedia.org" in url and "List_of_highest-grossing_films" in url:
                return await self._scrape_wikipedia_films(url)
            else:
                return await self._generic_web_scrape(url)

        except Exception as e:
            logger.error(f"Error scraping {url}: {str(e)}")
            return {"error": str(e), "data": None}

    async def _scrape_wikipedia_films(self, url: str) -> Dict[str, Any]:
        """Scrape Wikipedia highest grossing films data."""
        try:
            response = self.session.get(url)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, "html.parser")

            # Find the main table with film data
            tables = soup.find_all("table", class_="wikitable")

            films_data = []

            for table in tables:
                headers = []
                header_row = table.find("tr")
                if header_row:
                    headers = [
                        th.get_text().strip()
                        for th in header_row.find_all(["th", "td"])
                    ]

                if any("rank" in h.lower() for h in headers):
                    rows = table.find_all("tr")[1:]  # Skip header row

                    for row in rows:
                        cells = row.find_all(["td", "th"])
                        if len(cells) >= 4:
                            try:
                                rank_text = cells[0].get_text().strip()
                                title = cells[1].get_text().strip()
                                worldwide_gross = cells[2].get_text().strip()
                                year_text = cells[3].get_text().strip()

                                # Extract rank number
                                rank = int("".join(filter(str.isdigit, rank_text)) or 0)

                                # Extract year
                                year = int("".join(filter(str.isdigit, year_text)) or 0)

                                # Extract gross amount (remove $ and convert to float)
                                gross_clean = (
                                    worldwide_gross.replace("$", "")
                                    .replace(",", "")
                                    .replace(" billion", "000000000")
                                    .replace(" million", "000000")
                                )
                                gross = float(
                                    "".join(
                                        c
                                        for c in gross_clean
                                        if c.isdigit() or c == "."
                                    )
                                    or 0
                                )

                                # Convert millions/billions
                                if "billion" in worldwide_gross.lower():
                                    gross = gross * 1000000000
                                elif "million" in worldwide_gross.lower():
                                    gross = gross * 1000000

                                films_data.append(
                                    {
                                        "Rank": rank,
                                        "Title": title,
                                        "Worldwide_Gross": gross,
                                        "Year": year,
                                        "Peak": rank,  # Assuming Peak = Rank for this example
                                    }
                                )

                            except (ValueError, IndexError) as e:
                                continue

                    if films_data:  # If we found data, break
                        break

            df = pd.DataFrame(films_data)
            logger.info(f"Scraped {len(films_data)} films from Wikipedia")

            return {
                "data": df,
                "metadata": {
                    "source": url,
                    "rows": len(df),
                    "columns": list(df.columns) if not df.empty else [],
                },
            }

        except Exception as e:
            logger.error(f"Error scraping Wikipedia films: {str(e)}")
            return {"error": str(e), "data": None}

    async def _generic_web_scrape(self, url: str) -> Dict[str, Any]:
        """Generic web scraping for other sites."""
        try:
            response = self.session.get(url)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, "html.parser")

            # Extract tables
            tables = []
            for i, table in enumerate(soup.find_all("table")):
                table_data = []
                rows = table.find_all("tr")

                for row in rows:
                    cells = row.find_all(["td", "th"])
                    row_data = [cell.get_text().strip() for cell in cells]
                    if row_data:
                        table_data.append(row_data)

                if table_data:
                    tables.append(
                        {"index": i, "data": table_data, "rows": len(table_data)}
                    )

            return {
                "tables": tables,
                "text": soup.get_text()[:5000],  # First 5000 chars
                "metadata": {"url": url, "tables_found": len(tables)},
            }

        except Exception as e:
            logger.error(f"Error in generic web scraping: {str(e)}")
            return {"error": str(e), "data": None}

    async def load_data(self, file_path: str) -> Optional[pd.DataFrame]:
        """
        Load data from various file formats.

        Args:
            file_path: Path to the data file

        Returns:
            Pandas DataFrame or None if loading fails
        """
        try:
            _, ext = os.path.splitext(file_path.lower())

            if ext == ".csv":
                df = pd.read_csv(file_path)
            elif ext == ".json":
                df = pd.read_json(file_path)
            elif ext in [".xlsx", ".xls"]:
                df = pd.read_excel(file_path)
            elif ext == ".parquet":
                df = pd.read_parquet(file_path)
            else:
                logger.error(f"Unsupported file format: {ext}")
                return None

            logger.info(f"Loaded data from {file_path}: {df.shape}")
            return df

        except Exception as e:
            logger.error(f"Error loading data from {file_path}: {str(e)}")
            return None

    async def statistical_analysis(
        self, question: Dict[str, Any], data: pd.DataFrame
    ) -> Dict[str, Any]:
        """
        Perform statistical analysis on data.

        Args:
            question: Analysis question details
            data: DataFrame to analyze

        Returns:
            Analysis results
        """
        try:
            results = {}

            # Basic statistics
            results["basic_stats"] = {
                "shape": data.shape,
                "columns": list(data.columns),
                "dtypes": {col: str(dtype) for col, dtype in data.dtypes.items()},
                "null_counts": data.isnull().sum().to_dict(),
            }

            # Correlation analysis
            numeric_cols = data.select_dtypes(include=[np.number]).columns
            if len(numeric_cols) >= 2:
                correlation_matrix = data[numeric_cols].corr()
                results["correlations"] = correlation_matrix.to_dict()

            # Specific analysis based on question
            question_text = question.get("text", "").lower()

            if "correlation" in question_text:
                # Find correlation between specific columns mentioned
                for col1 in numeric_cols:
                    for col2 in numeric_cols:
                        if (
                            col1 != col2
                            and col1.lower() in question_text
                            and col2.lower() in question_text
                        ):
                            corr_val = data[col1].corr(data[col2])
                            results[f"correlation_{col1}_{col2}"] = corr_val

            if "regression" in question_text:
                # Simple linear regression
                for col1 in numeric_cols:
                    for col2 in numeric_cols:
                        if (
                            col1 != col2
                            and col1.lower() in question_text
                            and col2.lower() in question_text
                        ):
                            slope, intercept, r_value, p_value, std_err = (
                                stats.linregress(data[col1], data[col2])
                            )
                            results[f"regression_{col1}_{col2}"] = {
                                "slope": slope,
                                "intercept": intercept,
                                "r_value": r_value,
                                "p_value": p_value,
                                "std_err": std_err,
                            }

            return results

        except Exception as e:
            logger.error(f"Error in statistical analysis: {str(e)}")
            return {"error": str(e)}

    async def query_duckdb(self, query: str) -> Dict[str, Any]:
        """
        Execute DuckDB queries for large-scale data analysis.

        Args:
            query: SQL query to execute

        Returns:
            Query results
        """
        try:
            conn = duckdb.connect()
            result = conn.execute(query).fetchdf()
            conn.close()

            return {
                "data": result,
                "shape": result.shape,
                "columns": list(result.columns),
            }

        except Exception as e:
            logger.error(f"Error executing DuckDB query: {str(e)}")
            return {"error": str(e), "data": None}
