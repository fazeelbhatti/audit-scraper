from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Sequence

from . import __version__
from .scraper import collect_reports, download_reports, filter_reports, iter_report_dicts


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Download audit reports from https://agp.gov.pk/AuditReports",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("downloads"),
        help="Destination directory for downloaded reports (default: %(default)s).",
    )
    parser.add_argument(
        "--year",
        dest="years",
        nargs="+",
        help="Optional year labels or codes to filter (e.g. 2024-2025 or y14).",
    )
    parser.add_argument(
        "--query",
        help="Filter reports whose titles contain this substring (case-insensitive).",
    )
    parser.add_argument(
        "--limit",
        type=int,
        help="Limit the number of reports to process after filtering.",
    )
    parser.add_argument(
        "--max-workers",
        type=int,
        default=4,
        help="Number of concurrent downloads (default: %(default)s).",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Re-download files even if they already exist.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Skip actual downloads and just report which files would be fetched.",
    )
    parser.add_argument(
        "--metadata",
        type=Path,
        help="Optional path to write report metadata as JSON.",
    )
    parser.add_argument(
        "--list-only",
        action="store_true",
        help="Print a short summary of matched reports and exit without downloading.",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=60,
        help="HTTP timeout in seconds for download requests (default: %(default)s).",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        help="Logging level (DEBUG, INFO, WARNING, ERROR).",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"audit-scraper {__version__}",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)

    logging.basicConfig(
        level=getattr(logging, args.log_level.upper(), logging.INFO),
        format="%(levelname)s: %(message)s",
    )

    try:
        reports = collect_reports()
    except Exception as exc:  # pragma: no cover
        logging.error("Unable to collect reports: %s", exc)
        return 1

    if args.years or args.query:
        reports = filter_reports(reports, years=args.years, query=args.query)

    if args.limit is not None and args.limit >= 0:
        reports = reports[: args.limit]

    if not reports:
        logging.warning("No reports matched the given filters.")
        return 0

    logging.info("Selected %d reports for processing", len(reports))

    if args.metadata:
        args.metadata.parent.mkdir(parents=True, exist_ok=True)
        with args.metadata.open("w", encoding="utf-8") as handle:
            json.dump(list(iter_report_dicts(reports)), handle, ensure_ascii=False, indent=2)
        logging.info("Wrote metadata to %s", args.metadata)

    if args.list_only:
        for report in reports:
            print(f"{report.serial:04d} | {report.date_text} | {report.title}")
        return 0

    try:
        download_reports(
            reports,
            args.output,
            max_workers=args.max_workers,
            overwrite=args.overwrite,
            dry_run=args.dry_run,
            timeout=args.timeout,
        )
    except Exception as exc:  # pragma: no cover
        logging.error("Download failed: %s", exc)
        return 1

    action = "would be downloaded" if args.dry_run else "downloaded"
    logging.info("Successfully %s %d reports", action, len(reports))
    return 0


if __name__ == "__main__":
    sys.exit(main())
