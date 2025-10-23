"""HTML parsing utilities for the AGP audit reports listing."""

from __future__ import annotations

from typing import Iterable, List, Optional

from bs4 import BeautifulSoup

from .models import Report


def parse_reports(html: str) -> List[Report]:
    """Parse the HTML table of audit reports into a list of ``Report`` objects."""
    soup = BeautifulSoup(html, "html.parser")
    year_map = _extract_year_mapping(soup)

    rows = []
    for tr in soup.select("#myTable tbody tr"):
        report = _parse_row(tr, year_map)
        if report is not None:
            rows.append(report)
    return rows


def _extract_year_mapping(soup: BeautifulSoup) -> dict[str, str]:
    mapping: dict[str, str] = {}
    for option in soup.select("#year option"):
        value = option.get("value")
        text = option.text.strip()
        if not value or not text:
            continue
        mapping.setdefault(value.strip(), text)
    return mapping


def _parse_row(tr, year_map: dict[str, str]) -> Optional[Report]:
    cells = tr.find_all("td")
    if len(cells) < 4:
        return None

    try:
        serial = int(cells[0].get_text(strip=True))
    except ValueError:
        return None

    title = cells[1].get_text(" ", strip=True)
    date_text = cells[2].get_text(strip=True)

    link_tag = cells[3].find("a")
    href = link_tag.get("href") if link_tag else None
    if not href:
        return None

    year_code = _safe_cell_text(cells, 4)
    report_code = _safe_cell_text(cells, 5)
    type_code = _safe_cell_text(cells, 6)
    status_text = _safe_cell_text(cells, 7)
    is_active: Optional[bool] = None
    if status_text:
        lowered = status_text.lower()
        if lowered in {"true", "false"}:
            is_active = lowered == "true"

    return Report(
        serial=serial,
        title=title,
        date_text=date_text,
        download_url=href,
        year_code=year_code or None,
        year_label=year_map.get((year_code or "").strip()) if year_code else None,
        report_code=report_code or None,
        type_code=type_code or None,
        is_active=is_active,
    )


def _safe_cell_text(cells: Iterable, index: int) -> str:
    try:
        return cells[index].get_text(strip=True)
    except IndexError:
        return ""
