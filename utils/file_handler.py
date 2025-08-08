import os
import tempfile
import aiofiles
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


class FileHandler:
    """Handles file operations for the data analyst agent."""

    def __init__(self):
        self.supported_formats = {
            "text": [".txt", ".md", ".json"],
            "data": [".csv", ".xlsx", ".parquet", ".json"],
            "image": [".png", ".jpg", ".jpeg", ".gif", ".bmp"],
        }

    async def save_files(
        self, data_files: Dict[str, Dict[str, Any]], temp_dir: str
    ) -> Dict[str, str]:
        """
        Save uploaded files to temporary directory.

        Args:
            data_files: Dictionary of filename -> {content, content_type}
            temp_dir: Temporary directory path

        Returns:
            Dictionary of filename -> saved_file_path
        """
        saved_files = {}

        for filename, file_info in data_files.items():
            try:
                file_path = os.path.join(temp_dir, filename)

                # Write file content
                async with aiofiles.open(file_path, "wb") as f:
                    await f.write(file_info["content"])

                saved_files[filename] = file_path
                logger.info(f"Saved file: {filename} to {file_path}")

            except Exception as e:
                logger.error(f"Error saving file {filename}: {str(e)}")
                continue

        return saved_files

    def get_file_type(self, filename: str) -> str:
        """Determine file type based on extension."""
        _, ext = os.path.splitext(filename.lower())

        for file_type, extensions in self.supported_formats.items():
            if ext in extensions:
                return file_type

        return "unknown"

    def is_supported_format(self, filename: str) -> bool:
        """Check if file format is supported."""
        return self.get_file_type(filename) != "unknown"

    async def read_text_file(self, file_path: str) -> str:
        """Read text content from file."""
        try:
            async with aiofiles.open(file_path, "r", encoding="utf-8") as f:
                return await f.read()
        except Exception as e:
            logger.error(f"Error reading text file {file_path}: {str(e)}")
            return ""

    def get_file_info(self, file_path: str) -> Dict[str, Any]:
        """Get information about a file."""
        try:
            stat = os.stat(file_path)
            return {
                "size": stat.st_size,
                "modified": stat.st_mtime,
                "type": self.get_file_type(os.path.basename(file_path)),
                "exists": True,
            }
        except Exception as e:
            logger.error(f"Error getting file info for {file_path}: {str(e)}")
            return {"exists": False}
