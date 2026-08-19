"""
File Processor Port (Interface)

Abstract interface for handling the uploaded CV file on disk. Matching only ever
needs the file to exist somewhere the parser can read it, and to be gone again
afterwards, so this port is deliberately just those two operations.
"""

from abc import ABC, abstractmethod


class IFileProcessor(ABC):
    """Interface for temporary file handling."""

    @abstractmethod
    async def save_temp_file(self, content: bytes, suffix: str) -> str:
        """
        Write uploaded bytes to a temporary file.

        Args:
            content: Raw bytes of the uploaded file
            suffix: File extension to give the temp file, including the dot

        Returns:
            Path to the temporary file
        """
        pass

    @abstractmethod
    async def cleanup_file(self, file_path: str) -> None:
        """Delete a temporary file, ignoring the case where it is already gone."""
        pass
