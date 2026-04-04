"""
Document Loader Module

Handles loading medical documents from multiple sources:
- PubMed (via EUtils API)
- Local PDF files
- Structured markdown/text files
"""

import logging
import json
from abc import ABC, abstractmethod
from typing import List, Optional
from pathlib import Path

from .schemas import MedicalDocument

logger = logging.getLogger(__name__)


class DocumentLoader(ABC):
    """Abstract base class for document loaders"""

    @abstractmethod
    def load(self) -> List[MedicalDocument]:
        """Load documents from source"""
        pass


class PubMedLoader(DocumentLoader):
    """Load medical documents from PubMed via Entrez API"""

    def __init__(self, query: str, max_results: int = 100, email: str = "user@example.com"):
        """
        Initialize PubMed loader

        Args:
            query: PubMed search query (e.g., 'diabetes exercise type 2')
            max_results: Maximum number of papers to retrieve
            email: Email for NCBI API (required for high-volume requests)
        """
        try:
            from Bio import Entrez
        except ImportError:
            raise ImportError("Please install biopython: pip install biopython")

        self.query = query
        self.max_results = max_results
        self.email = email
        Entrez.email = email
        logger.info(f"Initialized PubMed loader for query: {query}")

    def load(self) -> List[MedicalDocument]:
        """Search PubMed and load documents"""
        from Bio import Entrez

        documents = []

        try:
            # Search
            logger.info(f"Searching PubMed for: {self.query}")
            search_handle = Entrez.esearch(db="pubmed", term=self.query, retmax=self.max_results)
            search_results = Entrez.read(search_handle)
            search_handle.close()

            pmids = search_results.get("IdList", [])
            logger.info(f"Found {len(pmids)} papers")

            if not pmids:
                logger.warning(f"No results found for query: {self.query}")
                return []

            # Fetch abstracts in batches
            batch_size = 10
            for i in range(0, len(pmids), batch_size):
                batch_pmids = pmids[i : i + batch_size]

                # Fetch details
                fetch_handle = Entrez.efetch(db="pubmed", id=",".join(batch_pmids), rettype="medline", retmode="text")
                records = fetch_handle.read()
                fetch_handle.close()

                # Parse MEDLINE format into documents
                docs_in_batch = self._parse_medline(records, batch_pmids)
                documents.extend(docs_in_batch)

                logger.info(f"Loaded {len(documents)} documents so far...")

        except Exception as e:
            logger.error(f"Error fetching from PubMed: {e}")
            return []

        logger.info(f"Loaded {len(documents)} documents from PubMed")
        return documents

    def _parse_medline(self, records: str, pmids: List[str]) -> List[MedicalDocument]:
        """Parse MEDLINE format records"""
        documents = []

        for pmid in pmids:
            # Try to find the record for this PMID
            if pmid not in records:
                continue

            # Extract blocks for this PMID
            title = self._extract_field(records, pmid, "TI")
            abstract = self._extract_field(records, pmid, "AB")
            authors = self._extract_field(records, pmid, "AU")
            publication_date = self._extract_field(records, pmid, "DP")

            content = f"{title}\n\n{abstract}" if abstract else title

            if content.strip():
                doc = MedicalDocument(
                    id=f"pubmed_{pmid}",
                    title=title or "Untitled",
                    content=content,
                    source="PubMed",
                    pubmed_id=pmid,
                    authors=[authors] if authors else None,
                    published_date=publication_date,
                )
                documents.append(doc)
                logger.debug(f"Parsed document: {doc.title[:60]}...")

        return documents

    @staticmethod
    def _extract_field(record: str, pmid: str, field: str) -> Optional[str]:
        """Extract field from MEDLINE record"""
        lines = record.split("\n")
        value = []

        for i, line in enumerate(lines):
            if line.startswith(field + "-") or line.startswith(field + " "):
                value.append(line[6:].strip())  # Skip field prefix (e.g., "AB- ")

        return " ".join(value) if value else None


class PDFLoader(DocumentLoader):
    """Load medical documents from PDF files"""

    def __init__(self, pdf_dir: Path):
        """
        Initialize PDF loader

        Args:
            pdf_dir: Directory containing PDF files
        """
        try:
            import pypdf
        except ImportError:
            raise ImportError("Please install pypdf: pip install pypdf")

        self.pdf_dir = Path(pdf_dir)
        if not self.pdf_dir.exists():
            logger.warning(f"PDF directory does not exist: {self.pdf_dir}")

        logger.info(f"Initialized PDF loader for directory: {pdf_dir}")

    def load(self) -> List[MedicalDocument]:
        """Load all PDFs from directory"""
        import pypdf

        documents = []

        if not self.pdf_dir.exists():
            logger.warning(f"PDF directory does not exist: {self.pdf_dir}")
            return []

        pdf_files = list(self.pdf_dir.glob("*.pdf"))
        logger.info(f"Found {len(pdf_files)} PDF files")

        for pdf_file in pdf_files:
            try:
                with open(pdf_file, "rb") as f:
                    reader = pypdf.PdfReader(f)

                    title = pdf_file.stem
                    full_text = ""

                    for page_num, page in enumerate(reader.pages):
                        text = page.extract_text()
                        full_text += f"\n[Page {page_num + 1}]\n{text}"

                    if full_text.strip():
                        doc = MedicalDocument(
                            id=f"pdf_{pdf_file.stem}",
                            title=title,
                            content=full_text,
                            source=f"PDF: {pdf_file.name}",
                        )
                        documents.append(doc)
                        logger.info(f"Loaded PDF: {title}")

            except Exception as e:
                logger.error(f"Error loading PDF {pdf_file}: {e}")

        logger.info(f"Loaded {len(documents)} documents from PDFs")
        return documents


class JSONLoader(DocumentLoader):
    """Load medical documents from JSON files"""

    def __init__(self, json_file: Path):
        """
        Initialize JSON loader

        Args:
            json_file: Path to JSON file containing documents
        """
        self.json_file = Path(json_file)
        logger.info(f"Initialized JSON loader for file: {json_file}")

    def load(self) -> List[MedicalDocument]:
        """Load documents from JSON file"""
        documents = []

        if not self.json_file.exists():
            logger.warning(f"JSON file does not exist: {self.json_file}")
            return []

        try:
            with open(self.json_file, "r") as f:
                data = json.load(f)

            # Handle different JSON structures
            if isinstance(data, list):
                items = data
            elif isinstance(data, dict) and "documents" in data:
                items = data["documents"]
            else:
                items = [data]

            for item in items:
                doc = MedicalDocument(**item) if isinstance(item, dict) else MedicalDocument(**item.__dict__)
                documents.append(doc)

            logger.info(f"Loaded {len(documents)} documents from JSON")
        except Exception as e:
            logger.error(f"Error loading JSON: {e}")

        return documents


class MarkdownLoader(DocumentLoader):
    """Load medical documents from Markdown files"""

    def __init__(self, md_dir: Path):
        """
        Initialize Markdown loader

        Args:
            md_dir: Directory containing markdown files
        """
        self.md_dir = Path(md_dir)
        if not self.md_dir.exists():
            logger.warning(f"Markdown directory does not exist: {self.md_dir}")

        logger.info(f"Initialized Markdown loader for directory: {md_dir}")

    def load(self) -> List[MedicalDocument]:
        """Load all markdown files from directory"""
        documents = []

        if not self.md_dir.exists():
            logger.warning(f"Markdown directory does not exist: {self.md_dir}")
            return []

        md_files = list(self.md_dir.glob("*.md"))
        logger.info(f"Found {len(md_files)} Markdown files")

        for md_file in md_files:
            try:
                with open(md_file, "r", encoding="utf-8") as f:
                    content = f.read()

                title = md_file.stem

                doc = MedicalDocument(
                    id=f"md_{md_file.stem}",
                    title=title,
                    content=content,
                    source=f"Markdown: {md_file.name}",
                )
                documents.append(doc)
                logger.info(f"Loaded Markdown: {title}")

            except Exception as e:
                logger.error(f"Error loading Markdown {md_file}: {e}")

        logger.info(f"Loaded {len(documents)} documents from Markdown files")
        return documents


def create_document_loader(loader_type: str, **kwargs) -> DocumentLoader:
    """
    Factory function to create document loader

    Args:
        loader_type: Type of loader ('pubmed', 'pdf', 'json', 'markdown')
        **kwargs: Arguments for loader constructor

    Returns:
        DocumentLoader instance
    """
    if loader_type.lower() == "pubmed":
        return PubMedLoader(**kwargs)
    elif loader_type.lower() == "pdf":
        pdf_dir = kwargs.get("pdf_dir", Path("backend/agents/rag/data/documents"))
        return PDFLoader(pdf_dir)
    elif loader_type.lower() == "json":
        json_file = kwargs.get("json_file")
        if not json_file:
            raise ValueError("json_file required for JSON loader")
        return JSONLoader(json_file)
    elif loader_type.lower() == "markdown":
        md_dir = kwargs.get("md_dir", Path("backend/agents/rag/data/documents"))
        return MarkdownLoader(md_dir)
    else:
        raise ValueError(f"Unknown document loader type: {loader_type}")
