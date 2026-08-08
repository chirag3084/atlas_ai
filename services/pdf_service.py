"""Extract selectable text from PDF earnings reports."""

from pypdf import PdfReader

import config


def extract_text(path: str) -> str:
    reader = PdfReader(path)
    parts = []
    for page in reader.pages:
        text = page.extract_text()
        if text:
            parts.append(text)
    full = "\n".join(parts)
    if len(full) > config.MAX_PDF_CHARS:
        full = full[: config.MAX_PDF_CHARS] + "\n… [truncated]"
    return full
