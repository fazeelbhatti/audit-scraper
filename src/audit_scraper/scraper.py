"""High level interface for collecting and downloading AGP audit reports."""

from __future__ import annotations

import concurrent.futures
import logging
import os
from dataclasses import asdict
from pathlib import Path
from typing import Iterable, Iterator, List, Optional, Sequence
from urllib.parse import urljoin

import requests

from .models import Report
from .parser import parse_reports

BASE_URL = "https://agp.gov.pk"
LISTING_URL = f"{BASE_URL}/AuditReports"
DEFAULT_TIMEOUT = 60

logger = logging.getLogger(__name__)


class ScraperError(Exception):
    """Base error raised when scraping fails."""


class DownloadError(ScraperError):
    """Raised when a report download fails."""


def fetch_listing(timeout: int = DEFAULT_TIMEOUT) -> str:
    """Download the HTML listing page."""
    logger.debug("Fetching listing page %s", LISTING_URL)
    response = requests.get(LISTING_URL, timeout=timeout)
    try:
        response.raise_for_status()
    except requests.HTTPError as exc:  # pragma: no cover - passthrough
        raise ScraperError(f"Failed to fetch listing page: {exc}") from exc
    response.encoding = response.apparent_encoding or "utf-8"
    return response.text


def collect_reports(html: Optional[str] = None) -> List[Report]:
    """Collect report metadata from the listing, optionally using cached HTML."""
    if html is None:
        html = fetch_listing()
    reports = parse_reports(html)
    logger.info("Parsed %d reports from listing", len(reports))
    return reports


def filter_reports(
    reports: Iterable[Report],
    *,
    years: Optional[Sequence[str]] = None,
    query: Optional[str] = None,
) -> List[Report]:
    """Apply optional filters by year label/code or title substring."""
    year_filter = None
    if years:
        normalized = {value.lower() for value in years}

        def year_filter(report: Report) -> bool:
            candidates = filter(None, [report.year_code, report.year_label])
            normalized_values = {value.lower() for value in candidates}
            return bool(normalized_values & normalized)

    query_filter = None
    if query:
        lowered = query.lower()

        def query_filter(report: Report) -> bool:
            return lowered in report.title.lower()

    filtered = []
    for report in reports:
        if year_filter and not year_filter(report):
            continue
        if query_filter and not query_filter(report):
            continue
        filtered.append(report)
    return filtered


def download_reports(
    reports: Sequence[Report],
    output_dir: Path,
    *,
    max_workers: int = os.cpu_count() or 4,
    overwrite: bool = False,
    dry_run: bool = False,
    timeout: int = DEFAULT_TIMEOUT,
) -> List[Path]:
    """Download all reports in ``reports`` to ``output_dir`` concurrently."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    logger.info("Preparing to download %d reports to %s", len(reports), output_dir)
    if dry_run:
        return [report.target_path(output_dir) for report in reports]

    saved_paths: List[Path] = []

    def worker(report: Report) -> Path:
        return _download_single(report, output_dir, overwrite=overwrite, timeout=timeout)

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_report = {executor.submit(worker, report): report for report in reports}
        for future in concurrent.futures.as_completed(future_to_report):
            report = future_to_report[future]
            try:
                path = future.result()
                saved_paths.append(path)
            except Exception as exc:  # pragma: no cover - ensures logging path
                logger.error("Failed to download report %s: %s", report.title, exc)
                raise
    return saved_paths


def iter_report_dicts(reports: Iterable[Report]) -> Iterator[dict]:
    """Yield plain dictionaries for each report, suitable for JSON serialization."""
    for report in reports:
        data = asdict(report)
        yield data


def _download_single(report: Report, output_dir: Path, *, overwrite: bool, timeout: int) -> Path:
    target_path = report.target_path(output_dir)
    target_path.parent.mkdir(parents=True, exist_ok=True)

    if target_path.exists() and not overwrite:
        logger.debug("Skipping existing file %s", target_path)
        return target_path

    url = urljoin(BASE_URL, report.download_url)
    logger.debug("Downloading %s -> %s", url, target_path)

    response = requests.get(url, stream=True, timeout=timeout)
    try:
        response.raise_for_status()
    except requests.HTTPError as exc:  # pragma: no cover - passthrough
        raise DownloadError(f"Failed to download {report.title}: {exc}") from exc

    with target_path.open("wb") as handle:
        for chunk in response.iter_content(chunk_size=128 * 1024):
            if chunk:
                handle.write(chunk)

    return target_path
