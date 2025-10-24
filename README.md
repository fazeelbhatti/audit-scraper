# AGP Audit Reports Scraper

This project provides a Python command-line tool that fetches the full list of audit reports published by the Auditor-General of Pakistan (AGP) at [https://agp.gov.pk/AuditReports](https://agp.gov.pk/AuditReports) and downloads the associated PDF files in bulk.

## Key features

- Scrapes all report metadata from the public listing table (no pagination required).
- Filters by year label/code or title substring before downloading.
- Concurrent downloads with optional dry-run mode.
- Saves structured metadata as JSON for further processing.
- Includes unit tests that validate HTML parsing and filename sanitisation logic.

## Requirements

- Python 3.9 or newer.
- Dependencies listed in `requirements.txt`.

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
python -m audit_scraper --output downloads
```

The scraper creates a `downloads/` directory (configurable) and populates it with sub-folders for each report year.

## Useful options

```bash
# Preview which files match the filters without downloading anything
python -m audit_scraper --dry-run --limit 5

# Download reports for a specific year label
python -m audit_scraper --year "2024-2025"

# Download only reports whose titles mention "covid"
python -m audit_scraper --query covid

# Write metadata to JSON while downloading
python -m audit_scraper --metadata reports.json
```

Run `python -m audit_scraper --help` to see the full list of command-line options.

## Running the tests

```bash
pytest
```

The tests use mocked HTML snippets so no network access is required.

Created by GPT5-Codex
