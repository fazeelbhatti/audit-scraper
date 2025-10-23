import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass(slots=True)
class Report:
    """Metadata describing a single audit report entry."""

    serial: int
    title: str
    date_text: str
    download_url: str
    year_code: Optional[str]
    year_label: Optional[str]
    report_code: Optional[str]
    type_code: Optional[str]
    is_active: Optional[bool]

    def target_path(self, base_dir: Path) -> Path:
        """Return the destination path for saving the report."""
        directory = base_dir
        if self.year_label:
            directory = directory / sanitize_directory_name(self.year_label)
        filename = sanitize_filename(f"{self.serial:04d}_{self.title}.pdf")
        return directory / filename

MAX_FILENAME_BYTES = 200


def sanitize_filename(name: str) -> str:
    """Sanitize a filename by replacing unsupported characters with underscores."""
    import re

    sanitized = _SANITIZE_TRANSLATION(name)
    sanitized = re.sub(r"_+", "_", sanitized)
    sanitized = re.sub(r"_+(\.)", r"\1", sanitized)
    sanitized = sanitized.strip("._ ")
    sanitized = sanitized or "report.pdf"

    encoded = sanitized.encode("utf-8")
    if len(encoded) <= MAX_FILENAME_BYTES:
        return sanitized

    stem, ext = os.path.splitext(sanitized)
    if not ext:
        ext = ".pdf"

    ext_bytes = ext.encode("utf-8")
    available = max(1, MAX_FILENAME_BYTES - len(ext_bytes))
    truncated_stem_bytes = stem.encode("utf-8")[:available]
    truncated_stem = truncated_stem_bytes.decode("utf-8", "ignore").rstrip("._ ")
    if not truncated_stem:
        truncated_stem = "report"

    return f"{truncated_stem}{ext}"


def sanitize_directory_name(name: str) -> str:
    """Sanitize directory names while preserving readability."""
    sanitized = _SANITIZE_TRANSLATION(name)
    sanitized = sanitized.strip("._ ")
    return sanitized or "Unknown-Year"


def _build_translation_table() -> callable:
    import re

    invalid_chars = r"[^A-Za-z0-9._-]+"
    pattern = re.compile(invalid_chars)

    def _sanitize(value: str) -> str:
        return pattern.sub("_", value)

    return _sanitize


_SANITIZE_TRANSLATION = _build_translation_table()
