import matplotlib.pyplot as plt
import matplotlib

matplotlib.use("Agg")  # Use non-interactive backend
import seaborn as sns
import pandas as pd
import numpy as np
from io import BytesIO
import base64
import os
from typing import Dict, Any, Optional
import logging
from scipy import stats

logger = logging.getLogger(__name__)


class VisualizationEngine:
    """Handles data visualization and chart generation."""

    def __init__(self):
        # Set up matplotlib styling
        plt.style.use("default")
        sns.set_palette("husl")

        # Configure matplotlib for better output
        plt.rcParams["figure.figsize"] = (10, 6)
        plt.rcParams["figure.dpi"] = 100
        plt.rcParams["savefig.dpi"] = 100
        plt.rcParams["savefig.bbox"] = "tight"

    async def create_visualization(
        self, question: Dict[str, Any], data: pd.DataFrame, temp_dir: str
    ) -> str:
        """
        Create visualization based on the question requirements.

        Args:
            question: Question details with visualization requirements
            data: DataFrame to visualize
            temp_dir: Temporary directory for saving files

        Returns:
            Base64 encoded image data URI
        """
        try:
            question_text = question["text"].lower()

            # Determine visualization type
            if "scatterplot" in question_text or "scatter plot" in question_text:
                return await self._create_scatterplot(question_text, data)
            elif "bar chart" in question_text or "bar plot" in question_text:
                return await self._create_bar_chart(question_text, data)
            elif "histogram" in question_text:
                return await self._create_histogram(question_text, data)
            elif "line plot" in question_text or "line chart" in question_text:
                return await self._create_line_plot(question_text, data)
            else:
                # Default to scatterplot for correlation/regression questions
                return await self._create_scatterplot(question_text, data)

        except Exception as e:
            logger.error(f"Error creating visualization: {str(e)}")
            return self._create_error_plot(str(e))

    async def _create_scatterplot(self, question_text: str, data: pd.DataFrame) -> str:
        """Create a scatterplot with optional regression line."""
        try:
            # Find numeric columns
            numeric_cols = data.select_dtypes(include=[np.number]).columns.tolist()

            if len(numeric_cols) < 2:
                return self._create_error_plot(
                    "Need at least 2 numeric columns for scatterplot"
                )

            # Try to identify x and y columns from question text
            x_col, y_col = self._identify_columns_from_text(question_text, numeric_cols)

            if not x_col or not y_col:
                # Use first two numeric columns as fallback
                x_col, y_col = numeric_cols[0], numeric_cols[1]

            # Create the plot
            fig, ax = plt.subplots(figsize=(10, 6))

            # Remove any infinite or very large values
            clean_data = (
                data[[x_col, y_col]].replace([np.inf, -np.inf], np.nan).dropna()
            )

            if clean_data.empty:
                return self._create_error_plot("No valid data points for visualization")

            # Create scatterplot
            ax.scatter(clean_data[x_col], clean_data[y_col], alpha=0.6, s=50)

            # Add regression line if requested
            if "regression" in question_text or "dotted" in question_text:
                try:
                    # Calculate regression line
                    slope, intercept, r_value, p_value, std_err = stats.linregress(
                        clean_data[x_col], clean_data[y_col]
                    )

                    # Create regression line
                    x_range = np.array(
                        [clean_data[x_col].min(), clean_data[x_col].max()]
                    )
                    y_range = slope * x_range + intercept

                    # Plot regression line
                    line_style = ":" if "dotted" in question_text else "-"
                    line_color = "red" if "red" in question_text else "blue"
                    ax.plot(
                        x_range,
                        y_range,
                        line_style,
                        color=line_color,
                        linewidth=2,
                        label=f"Regression Line (R² = {r_value**2:.3f})",
                    )

                    ax.legend()

                except Exception as e:
                    logger.warning(f"Could not add regression line: {str(e)}")

            # Set labels and title
            ax.set_xlabel(x_col)
            ax.set_ylabel(y_col)
            ax.set_title(f"{y_col} vs {x_col}")
            ax.grid(True, alpha=0.3)

            # Convert to base64
            return self._fig_to_base64(fig)

        except Exception as e:
            logger.error(f"Error creating scatterplot: {str(e)}")
            return self._create_error_plot(str(e))

    async def _create_bar_chart(self, question_text: str, data: pd.DataFrame) -> str:
        """Create a bar chart."""
        try:
            # Find categorical and numeric columns
            cat_cols = data.select_dtypes(
                include=["object", "category"]
            ).columns.tolist()
            num_cols = data.select_dtypes(include=[np.number]).columns.tolist()

            if not cat_cols or not num_cols:
                return self._create_error_plot(
                    "Need categorical and numeric columns for bar chart"
                )

            x_col = cat_cols[0]
            y_col = num_cols[0]

            # Create the plot
            fig, ax = plt.subplots(figsize=(12, 6))

            # Aggregate data if needed
            plot_data = data.groupby(x_col)[y_col].mean().sort_values(ascending=False)

            # Limit to top 20 categories for readability
            if len(plot_data) > 20:
                plot_data = plot_data.head(20)

            bars = ax.bar(range(len(plot_data)), plot_data.values)
            ax.set_xticks(range(len(plot_data)))
            ax.set_xticklabels(plot_data.index, rotation=45, ha="right")

            ax.set_xlabel(x_col)
            ax.set_ylabel(f"Average {y_col}")
            ax.set_title(f"Average {y_col} by {x_col}")
            ax.grid(True, alpha=0.3)

            return self._fig_to_base64(fig)

        except Exception as e:
            logger.error(f"Error creating bar chart: {str(e)}")
            return self._create_error_plot(str(e))

    async def _create_histogram(self, question_text: str, data: pd.DataFrame) -> str:
        """Create a histogram."""
        try:
            numeric_cols = data.select_dtypes(include=[np.number]).columns.tolist()

            if not numeric_cols:
                return self._create_error_plot("Need numeric columns for histogram")

            col = numeric_cols[0]  # Use first numeric column

            fig, ax = plt.subplots(figsize=(10, 6))

            # Remove infinite values
            clean_data = data[col].replace([np.inf, -np.inf], np.nan).dropna()

            ax.hist(clean_data, bins=30, alpha=0.7, edgecolor="black")
            ax.set_xlabel(col)
            ax.set_ylabel("Frequency")
            ax.set_title(f"Distribution of {col}")
            ax.grid(True, alpha=0.3)

            return self._fig_to_base64(fig)

        except Exception as e:
            logger.error(f"Error creating histogram: {str(e)}")
            return self._create_error_plot(str(e))

    async def _create_line_plot(self, question_text: str, data: pd.DataFrame) -> str:
        """Create a line plot."""
        try:
            numeric_cols = data.select_dtypes(include=[np.number]).columns.tolist()

            if len(numeric_cols) < 2:
                return self._create_error_plot(
                    "Need at least 2 numeric columns for line plot"
                )

            x_col, y_col = numeric_cols[0], numeric_cols[1]

            fig, ax = plt.subplots(figsize=(10, 6))

            # Sort data by x column
            sorted_data = data.sort_values(x_col)
            clean_data = (
                sorted_data[[x_col, y_col]].replace([np.inf, -np.inf], np.nan).dropna()
            )

            ax.plot(clean_data[x_col], clean_data[y_col], marker="o", markersize=4)
            ax.set_xlabel(x_col)
            ax.set_ylabel(y_col)
            ax.set_title(f"{y_col} vs {x_col}")
            ax.grid(True, alpha=0.3)

            return self._fig_to_base64(fig)

        except Exception as e:
            logger.error(f"Error creating line plot: {str(e)}")
            return self._create_error_plot(str(e))

    def _identify_columns_from_text(self, question_text: str, columns: list) -> tuple:
        """Try to identify which columns to use based on question text."""
        x_col, y_col = None, None

        # Look for column names in question text
        question_lower = question_text.lower()

        for col in columns:
            col_lower = col.lower()
            if col_lower in question_lower:
                if "rank" in col_lower and (
                    "x" in question_lower or "x-axis" in question_lower
                ):
                    x_col = col
                elif "peak" in col_lower and (
                    "y" in question_lower or "y-axis" in question_lower
                ):
                    y_col = col
                elif not x_col:
                    x_col = col
                elif not y_col:
                    y_col = col

        return x_col, y_col

    def _fig_to_base64(self, fig) -> str:
        """Convert matplotlib figure to base64 encoded data URI."""
        try:
            # Save to bytes
            buffer = BytesIO()
            fig.savefig(buffer, format="png", bbox_inches="tight", dpi=100)
            buffer.seek(0)

            # Encode to base64
            img_data = base64.b64encode(buffer.read()).decode()

            # Create data URI
            data_uri = f"data:image/png;base64,{img_data}"

            plt.close(fig)  # Clean up

            # Check size (should be under 100KB)
            if len(data_uri) > 100000:
                logger.warning(
                    f"Image size ({len(data_uri)} bytes) exceeds 100KB limit"
                )

            return data_uri

        except Exception as e:
            logger.error(f"Error converting figure to base64: {str(e)}")
            plt.close(fig)
            return self._create_error_plot(str(e))

    def _create_error_plot(self, error_message: str) -> str:
        """Create a simple error plot."""
        try:
            fig, ax = plt.subplots(figsize=(8, 4))
            ax.text(
                0.5,
                0.5,
                f"Error creating plot:\n{error_message}",
                ha="center",
                va="center",
                transform=ax.transAxes,
                bbox=dict(boxstyle="round,pad=0.3", facecolor="lightcoral"),
            )
            ax.set_xlim(0, 1)
            ax.set_ylim(0, 1)
            ax.axis("off")

            return self._fig_to_base64(fig)

        except Exception as e:
            logger.error(f"Error creating error plot: {str(e)}")
            return "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=="
