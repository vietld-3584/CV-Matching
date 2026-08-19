"""
Azure Document Intelligence Adapter

Implements IDocumentParser using Azure Document Intelligence. It reads PDF, DOCX
and image CVs directly, so no conversion step is needed before OCR.
"""

import asyncio
import os
from typing import Optional

from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.ai.documentintelligence.models import AnalyzeResult
from azure.core.credentials import AzureKeyCredential

from cv_matching.src.domain.ports.document_parser import IDocumentParser
from cv_matching.src.infrastructure.config.settings import AzureDocumentIntelligenceSettings


class AzureDocumentParser(IDocumentParser):
    """Azure Document Intelligence implementation of the document parser port."""

    def __init__(self, settings: AzureDocumentIntelligenceSettings):
        """
        Args:
            settings: Azure Document Intelligence configuration
        """
        self.settings = settings
        self._client = None

        # Only initialize client if credentials are provided
        if settings.endpoint and settings.key:
            self._client = DocumentIntelligenceClient(
                endpoint=settings.endpoint,
                credential=AzureKeyCredential(settings.key),
                headers={"x-ms-region": settings.region},
            )

    async def extract_text(self, file_path: str, model_id: Optional[str] = None) -> str:
        """
        Extract text from a CV file using Azure DI.

        Args:
            file_path: Path to the CV file
            model_id: Azure model ID (default: "prebuilt-read")

        Returns:
            Extracted text content

        Raises:
            RuntimeError: If the client was never configured
            FileNotFoundError: If the file does not exist
        """
        if not self._client:
            raise RuntimeError(
                "Azure Document Intelligence client not initialized. "
                "Check AZURE__ENDPOINT and AZURE__KEY in .env"
            )

        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        model = model_id or "prebuilt-read"

        def _analyze() -> AnalyzeResult:
            with open(file_path, "rb") as document:
                poller = self._client.begin_analyze_document(
                    model_id=model,
                    body=document,
                    content_type="application/octet-stream",
                )
                return poller.result()

        # The Azure client is synchronous. Moving the full polling lifecycle to a worker
        # prevents a slow OCR request from blocking FastAPI's event loop.
        result = await asyncio.to_thread(_analyze)
        return self._format_result(result)

    def _format_result(self, result: AnalyzeResult) -> str:
        """Format an Azure DI result into readable text."""
        all_text = []

        for page in result.pages:
            # Add page separator for multi-page documents
            if page.page_number > 1:
                all_text.append(f"\n{'=' * 80}\n")
                all_text.append(f"PAGE {page.page_number}\n")
                all_text.append(f"{'=' * 80}\n\n")

            # Extract text from lines
            for line in page.lines:
                all_text.append(line.content)

        return "\n".join(all_text)
