"""
Document Parser Port (Interface)

Abstract interface for extracting the raw text of a CV file. The container
wires this to the Azure Document Intelligence adapter already used by the
doc analyzer, but any OCR backend fits.
"""

from abc import ABC, abstractmethod
from typing import Optional


class IDocumentParser(ABC):
    """Interface for CV text extraction."""

    @abstractmethod
    async def extract_text(self, file_path: str, model_id: Optional[str] = None) -> str:
        """
        Extract text content from a CV file.

        Args:
            file_path: Path to the CV file
            model_id: Optional specific model to use

        Returns:
            Extracted text content

        Raises:
            FileNotFoundError: If file doesn't exist
        """
        pass
