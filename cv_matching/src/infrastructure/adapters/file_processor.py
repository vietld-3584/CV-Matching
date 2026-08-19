"""
File Processor Adapter

Holds an uploaded CV on disk for as long as the parser needs it.

Azure Document Intelligence reads PDF, DOCX and image files directly, so unlike a
vision based pipeline this service never has to rasterise or downscale anything -
the file is written once, read once and deleted.
"""

import asyncio
import os
import tempfile

from cv_matching.src.domain.ports.file_processor import IFileProcessor


class FileProcessor(IFileProcessor):
    """Temporary file handling backed by the local filesystem."""

    async def save_temp_file(self, content: bytes, suffix: str) -> str:
        def _write() -> str:
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                tmp.write(content)
                return tmp.name

        return await asyncio.to_thread(_write)

    async def cleanup_file(self, file_path: str) -> None:
        # Cleanup runs as a background task after the response has been sent, so a
        # failure here must not surface as an error the caller can no longer act on.
        try:
            if os.path.exists(file_path):
                os.unlink(file_path)
        except OSError:
            pass
