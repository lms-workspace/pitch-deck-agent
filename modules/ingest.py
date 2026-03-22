"""
Document Ingestion Module

Handles parsing of all supported file types:
  - PDF  → PyMuPDF text extraction + Gemini vision for scanned/image PDFs
  - Image → Gemini vision description
  - Text  → Direct read (.txt, .md, .rtf)
  - Email → .eml parsing (headers + body + attachment extraction)
  - Video → Frame extraction + Whisper transcription (Phase 2)

All parsers return IngestedDocument objects that feed into the synthesis pipeline.
"""
from __future__ import annotations

import base64
import email
import io
import mimetypes
import tempfile
from email import policy
from pathlib import Path
from typing import BinaryIO

import fitz  # PyMuPDF
from loguru import logger
from PIL import Image

from core.models import FileType, IngestedDocument, IngestResult
from config import (
    MAX_FILE_SIZE_MB,
    MAX_PDF_PAGES,
    SUPPORTED_EXTENSIONS,
    GEMINI_API_KEY,
    GEMINI_MODEL,
)

# ── Gemini Client (lazy init) ────────────────────────────────────────

_gemini_model = None


def _get_gemini():
    """Lazy-initialize Gemini client."""
    global _gemini_model
    if _gemini_model is None:
        import google.generativeai as genai
        genai.configure(api_key=GEMINI_API_KEY)
        _gemini_model = genai.GenerativeModel(GEMINI_MODEL)
    return _gemini_model


# ── File Type Detection ───────────────────────────────────────────────

def detect_file_type(filename: str, content_bytes: bytes | None = None) -> FileType:
    """Determine FileType from extension and optional MIME sniffing."""
    ext = Path(filename).suffix.lower()

    for ftype, extensions in SUPPORTED_EXTENSIONS.items():
        if ext in extensions:
            return FileType(ftype.rstrip("s"))  # "documents" → "document" won't work
    
    # Map category to FileType
    ext_map = {}
    for category, exts in SUPPORTED_EXTENSIONS.items():
        for e in exts:
            if category == "documents":
                ext_map[e] = FileType.PDF if e == ".pdf" else FileType.TEXT
            elif category == "emails":
                ext_map[e] = FileType.EMAIL
            elif category == "images":
                ext_map[e] = FileType.IMAGE
            elif category == "video":
                ext_map[e] = FileType.VIDEO

    return ext_map.get(ext, FileType.UNKNOWN)


def validate_file(filename: str, size_bytes: int) -> str | None:
    """Return error message if file is invalid, else None."""
    ext = Path(filename).suffix.lower()
    all_exts = []
    for exts in SUPPORTED_EXTENSIONS.values():
        all_exts.extend(exts)

    if ext not in all_exts:
        return f"Unsupported file type: {ext}. Supported: {', '.join(all_exts)}"

    if size_bytes > MAX_FILE_SIZE_MB * 1024 * 1024:
        return f"File too large: {size_bytes / 1024 / 1024:.1f}MB (max {MAX_FILE_SIZE_MB}MB)"

    return None


# ── PDF Parser ────────────────────────────────────────────────────────

def parse_pdf(filename: str, file_bytes: bytes) -> IngestedDocument:
    """
    Extract text from PDF using PyMuPDF.
    Falls back to Gemini vision for scanned/image-heavy PDFs.
    """
    logger.info(f"Parsing PDF: {filename}")
    doc = fitz.open(stream=file_bytes, filetype="pdf")
    page_count = min(len(doc), MAX_PDF_PAGES)

    text_parts = []
    image_descriptions = []
    total_text_len = 0

    for page_num in range(page_count):
        page = doc[page_num]
        page_text = page.get_text("text").strip()
        total_text_len += len(page_text)

        if page_text:
            text_parts.append(f"[Page {page_num + 1}]\n{page_text}")

    doc.close()

    # If very little text extracted, it's likely a scanned PDF → use Gemini
    if total_text_len < 200 and GEMINI_API_KEY:
        logger.info(f"Low text yield ({total_text_len} chars), using Gemini vision on PDF")
        try:
            gemini_text, gemini_descs = _parse_pdf_with_gemini(file_bytes)
            if gemini_text:
                text_parts = [gemini_text]
            image_descriptions.extend(gemini_descs)
        except Exception as e:
            logger.warning(f"Gemini PDF fallback failed: {e}")

    extracted = "\n\n".join(text_parts)

    return IngestedDocument(
        filename=filename,
        file_type=FileType.PDF,
        extracted_text=extracted,
        page_count=page_count,
        image_descriptions=image_descriptions,
        metadata={"original_page_count": page_count},
        raw_content_preview=extracted[:500],
    )


def _parse_pdf_with_gemini(file_bytes: bytes) -> tuple[str, list[str]]:
    """Use Gemini 2.0 Flash to extract content from a scanned/image PDF."""
    model = _get_gemini()

    # Gemini can handle PDF bytes directly via the file API
    # For inline, we convert pages to images
    doc = fitz.open(stream=file_bytes, filetype="pdf")
    images = []
    for page_num in range(min(len(doc), 10)):  # Cap at 10 pages for Gemini
        page = doc[page_num]
        pix = page.get_pixmap(dpi=150)
        img_bytes = pix.tobytes("png")
        images.append({
            "mime_type": "image/png",
            "data": base64.b64encode(img_bytes).decode(),
        })
    doc.close()

    if not images:
        return "", []

    prompt = (
        "Extract ALL text content from these PDF pages. Maintain the original structure, "
        "headings, and formatting as much as possible. If there are images, describe them. "
        "If this is a script or screenplay, preserve the formatting (scene headings, "
        "action lines, dialogue with character names)."
    )

    parts = [prompt]
    for img in images:
        parts.append({"inline_data": img})

    response = model.generate_content(parts)
    text = response.text if response.text else ""

    return text, []


# ── Image Parser ──────────────────────────────────────────────────────

def parse_image(filename: str, file_bytes: bytes) -> IngestedDocument:
    """Use Gemini vision to describe an image for narrative context."""
    logger.info(f"Parsing image: {filename}")

    description = ""
    if GEMINI_API_KEY:
        try:
            description = _describe_image_with_gemini(file_bytes, filename)
        except Exception as e:
            logger.warning(f"Gemini image description failed: {e}")

    # Fallback: basic image metadata
    try:
        img = Image.open(io.BytesIO(file_bytes))
        metadata = {
            "size": img.size,
            "format": img.format,
            "mode": img.mode,
        }
    except Exception:
        metadata = {}

    return IngestedDocument(
        filename=filename,
        file_type=FileType.IMAGE,
        extracted_text=description,
        image_descriptions=[description] if description else [],
        metadata=metadata,
        raw_content_preview=description[:500],
    )


def _describe_image_with_gemini(file_bytes: bytes, filename: str) -> str:
    """Get Gemini to describe an image in narrative/creative context."""
    model = _get_gemini()

    mime_type = mimetypes.guess_type(filename)[0] or "image/png"

    prompt = (
        "You are analyzing this image as part of a creative pitch deck project. "
        "Describe what you see in detail, focusing on:\n"
        "- Characters/people depicted\n"
        "- Setting and environment\n"
        "- Mood, tone, and visual style\n"
        "- Any text visible in the image\n"
        "- How this image might relate to a story or narrative\n"
        "Be specific and vivid in your description."
    )

    response = model.generate_content([
        prompt,
        {"inline_data": {"mime_type": mime_type, "data": base64.b64encode(file_bytes).decode()}},
    ])

    return response.text if response.text else ""


# ── Text Parser ───────────────────────────────────────────────────────

def parse_text(filename: str, file_bytes: bytes) -> IngestedDocument:
    """Parse plain text, markdown, or RTF files."""
    logger.info(f"Parsing text file: {filename}")

    # Try common encodings
    text = ""
    for encoding in ["utf-8", "utf-16", "latin-1", "cp1252"]:
        try:
            text = file_bytes.decode(encoding)
            break
        except (UnicodeDecodeError, Exception):
            continue

    if not text:
        text = file_bytes.decode("utf-8", errors="replace")

    return IngestedDocument(
        filename=filename,
        file_type=FileType.TEXT,
        extracted_text=text,
        page_count=1,
        metadata={"encoding": "auto-detected", "char_count": len(text)},
        raw_content_preview=text[:500],
    )


# ── Email Parser ──────────────────────────────────────────────────────

def parse_email(filename: str, file_bytes: bytes) -> IngestedDocument:
    """
    Parse .eml files extracting headers, body text, and noting attachments.
    """
    logger.info(f"Parsing email: {filename}")

    msg = email.message_from_bytes(file_bytes, policy=policy.default)

    # Extract headers
    headers = {
        "from": str(msg.get("From", "")),
        "to": str(msg.get("To", "")),
        "cc": str(msg.get("Cc", "")),
        "subject": str(msg.get("Subject", "")),
        "date": str(msg.get("Date", "")),
    }

    # Extract body
    body_parts = []
    attachments = []

    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            disposition = str(part.get("Content-Disposition", ""))

            if "attachment" in disposition:
                att_filename = part.get_filename() or "unnamed_attachment"
                attachments.append(att_filename)
                continue

            if content_type == "text/plain":
                payload = part.get_payload(decode=True)
                if payload:
                    body_parts.append(payload.decode("utf-8", errors="replace"))
            elif content_type == "text/html" and not body_parts:
                # Only use HTML if no plain text found
                payload = part.get_payload(decode=True)
                if payload:
                    # Basic HTML stripping
                    import re
                    html_text = payload.decode("utf-8", errors="replace")
                    clean = re.sub(r"<[^>]+>", " ", html_text)
                    clean = re.sub(r"\s+", " ", clean).strip()
                    body_parts.append(clean)
    else:
        payload = msg.get_payload(decode=True)
        if payload:
            body_parts.append(payload.decode("utf-8", errors="replace"))

    body = "\n".join(body_parts)

    # Format as structured text
    formatted = (
        f"EMAIL\n"
        f"From: {headers['from']}\n"
        f"To: {headers['to']}\n"
        f"CC: {headers['cc']}\n"
        f"Date: {headers['date']}\n"
        f"Subject: {headers['subject']}\n"
        f"{'─' * 40}\n"
        f"{body}"
    )

    if attachments:
        formatted += f"\n\n[Attachments: {', '.join(attachments)}]"

    return IngestedDocument(
        filename=filename,
        file_type=FileType.EMAIL,
        extracted_text=formatted,
        page_count=1,
        metadata={**headers, "attachment_count": len(attachments), "attachments": attachments},
        raw_content_preview=formatted[:500],
    )


# ── Video Parser (Phase 2 stub) ──────────────────────────────────────

def parse_video(filename: str, file_bytes: bytes) -> IngestedDocument:
    """
    Phase 2: Extract key frames + Whisper transcription.
    Currently returns a placeholder.
    """
    logger.info(f"Video parsing not yet implemented: {filename}")
    return IngestedDocument(
        filename=filename,
        file_type=FileType.VIDEO,
        extracted_text="[Video file — transcription pending Phase 2 implementation]",
        metadata={"status": "not_implemented"},
        raw_content_preview="[Video file]",
    )


# ── Main Ingestion Orchestrator ───────────────────────────────────────

PARSER_MAP = {
    FileType.PDF: parse_pdf,
    FileType.IMAGE: parse_image,
    FileType.TEXT: parse_text,
    FileType.EMAIL: parse_email,
    FileType.VIDEO: parse_video,
}


def ingest_file(filename: str, file_bytes: bytes) -> IngestedDocument:
    """Parse a single file and return an IngestedDocument."""
    file_type = detect_file_type(filename)

    validation_error = validate_file(filename, len(file_bytes))
    if validation_error:
        logger.error(f"Validation failed for {filename}: {validation_error}")
        return IngestedDocument(
            filename=filename,
            file_type=file_type,
            extracted_text="",
            metadata={"error": validation_error},
        )

    parser = PARSER_MAP.get(file_type)
    if not parser:
        logger.warning(f"No parser for file type: {file_type} ({filename})")
        return IngestedDocument(
            filename=filename,
            file_type=FileType.UNKNOWN,
            metadata={"error": f"Unsupported file type: {file_type}"},
        )

    try:
        return parser(filename, file_bytes)
    except Exception as e:
        logger.exception(f"Failed to parse {filename}")
        return IngestedDocument(
            filename=filename,
            file_type=file_type,
            metadata={"error": str(e)},
        )


def ingest_files(files: list[tuple[str, bytes]]) -> IngestResult:
    """
    Ingest multiple files and return aggregated results.

    Args:
        files: List of (filename, file_bytes) tuples.
               In Gradio, these come from gr.File components.

    Returns:
        IngestResult with all parsed documents and error tracking.
    """
    result = IngestResult(total_files=len(files))

    for filename, file_bytes in files:
        logger.info(f"Ingesting: {filename} ({len(file_bytes)} bytes)")
        doc = ingest_file(filename, file_bytes)

        if doc.metadata.get("error"):
            result.errors.append(f"{filename}: {doc.metadata['error']}")
        else:
            result.documents.append(doc)
            result.total_text_chars += len(doc.extracted_text)

    logger.info(
        f"Ingestion complete: {len(result.documents)}/{result.total_files} files parsed, "
        f"{result.total_text_chars} total chars, {len(result.errors)} errors"
    )
    return result


def ingest_from_gradio(uploaded_files) -> IngestResult:
    """
    Convenience wrapper for Gradio file uploads.
    Gradio provides file objects with .name attribute and readable content.
    """
    file_tuples = []
    for f in uploaded_files:
        if hasattr(f, "name"):
            filepath = Path(f.name) if isinstance(f.name, str) else Path(str(f))
            file_bytes = filepath.read_bytes()
            file_tuples.append((filepath.name, file_bytes))
        elif isinstance(f, (str, Path)):
            filepath = Path(f)
            file_bytes = filepath.read_bytes()
            file_tuples.append((filepath.name, file_bytes))

    return ingest_files(file_tuples)
