"""
Typed schemas for browser agent output.
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class FileDetail(BaseModel):
    """
    Details about a downloaded or created file.
    """

    path: str = Field(description="Absolute path to the file")
    name: str = Field(description="File name with extension")
    size: int = Field(description="File size in bytes")


class BrowserOutput(BaseModel):
    """
    Structured output from browser agent with file tracking.
    """

    text: str = Field(description="Summary of what the browser accomplished")
    files: List[str] = Field(
        default_factory=list, description="List of absolute file paths"
    )
    file_details: List[FileDetail] = Field(
        default_factory=list, description="Detailed information about each file"
    )
    work_directory: Optional[str] = Field(
        default=None, description="Working directory where files were saved"
    )

    def has_files(self) -> bool:
        """Check if any files were downloaded/created."""
        return len(self.files) > 0

    def get_file_count(self) -> int:
        """Get the number of files."""
        return len(self.files)

    def get_total_size_kb(self) -> float:
        """Get total size of all files in KB."""
        return sum(f.size for f in self.file_details) / 1024

    def format_summary(self) -> str:
        """
        Format a human-readable summary of the browser output.
        """
        summary = f"📝 {self.text}\n"
        if self.has_files():
            summary += f"\n📁 Downloaded {self.get_file_count()} file(s):\n"
            for detail in self.file_details:
                size_kb = detail.size / 1024
                summary += f"   • {detail.name} ({size_kb:.1f} KB)\n"
                summary += f"     Path: {detail.path}\n"
        return summary
