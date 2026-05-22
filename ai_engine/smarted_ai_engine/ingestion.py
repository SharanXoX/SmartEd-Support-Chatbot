"""Split and normalize text from PDF, DOCX, Markdown, HTML snippets."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Iterable

from bs4 import BeautifulSoup
from docx import Document as DocxDocument
from markdown_it import MarkdownIt
from pypdf import PdfReader


def _chunks(text: str, max_chars: int = 1200, overlap: int = 150) -> list[str]:
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        return []
    pieces: list[str] = []
    start = 0
    while start < len(text):
        end = min(len(text), start + max_chars)
        piece = text[start:end]
        pieces.append(piece)
        if end == len(text):
            break
        start = max(0, end - overlap)
    return pieces


def extract_pdf(path: Path) -> str:
    reader = PdfReader(str(path))
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def extract_docx(path: Path) -> str:
    doc = DocxDocument(str(path))
    return "\n".join(p.text for p in doc.paragraphs if p.text)


def extract_markdown(path: Path) -> str:
    md = MarkdownIt().enable("table")
    raw = path.read_text(encoding="utf-8", errors="ignore")
    html = md.render(raw)
    return BeautifulSoup(html, "html.parser").get_text(" ", strip=True)


def extract_html(path: Path) -> str:
    return BeautifulSoup(path.read_text(encoding="utf-8", errors="ignore"), "html.parser").get_text(
        " ", strip=True
    )


def extract_plain(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def load_document_text(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        return extract_pdf(path)
    if suffix == ".docx":
        return extract_docx(path)
    if suffix in {".md", ".markdown"}:
        return extract_markdown(path)
    if suffix in {".html", ".htm"}:
        return extract_html(path)
    return extract_plain(path)


def ingest_text_chunks(text: str) -> tuple[list[str], list[dict[str, str]]]:
    parts = _chunks(text)
    metas = [{"chunk_index": str(i)} for i in range(len(parts))]
    return parts, metas


def iter_files(paths: Iterable[Path]) -> list[Path]:
    out: list[Path] = []
    for p in paths:
        if p.is_file():
            out.append(p)
        elif p.is_dir():
            for child in sorted(p.rglob("*")):
                if child.is_file() and child.suffix.lower() in {
                    ".pdf",
                    ".docx",
                    ".md",
                    ".markdown",
                    ".txt",
                    ".html",
                    ".htm",
                }:
                    out.append(child)
    return out
