from __future__ import annotations

from pathlib import Path

import pytest

from audit_scraper.models import Report, sanitize_directory_name, sanitize_filename
from audit_scraper.parser import parse_reports
from audit_scraper.scraper import filter_reports


@pytest.fixture()
def sample_html() -> str:
    return """
    <select id="year">
        <option value=""> Select Year</option>
        <option value="y1">2009 downwards</option>
        <option value="y2">2010-2011</option>
    </select>
    <table id="myTable">
        <tbody>
            <tr>
                <td>1</td>
                <td>First <strong>Report</strong> Title</td>
                <td>January 01, 2020</td>
                <td><a href="/SiteImage/Policy/report-1.pdf">Download</a></td>
                <td hidden>y2</td>
                <td hidden>ar1</td>
                <td hidden>7</td>
                <td hidden>True</td>
            </tr>
            <tr>
                <td>2</td>
                <td>Second Report</td>
                <td>February 02, 2019</td>
                <td><a href="/SiteImage/Policy/report-2.pdf">Download</a></td>
                <td hidden>y1</td>
                <td hidden>ar2</td>
                <td hidden>6</td>
                <td hidden>False</td>
            </tr>
        </tbody>
    </table>
    """


def test_parse_reports(sample_html: str) -> None:
    reports = parse_reports(sample_html)
    assert len(reports) == 2

    first = reports[0]
    assert first.serial == 1
    assert first.title == "First Report Title"
    assert first.download_url == "/SiteImage/Policy/report-1.pdf"
    assert first.year_code == "y2"
    assert first.year_label == "2010-2011"
    assert first.is_active is True

    second = reports[1]
    assert second.serial == 2
    assert second.year_label == "2009 downwards"
    assert second.is_active is False


def test_filter_reports_by_year(sample_html: str) -> None:
    reports = parse_reports(sample_html)
    filtered = filter_reports(reports, years=["y2"])
    assert [r.serial for r in filtered] == [1]

    filtered_by_label = filter_reports(reports, years=["2010-2011"])
    assert [r.serial for r in filtered_by_label] == [1]


def test_target_path_sanitization(tmp_path: Path) -> None:
    report = Report(
        serial=3,
        title="Report with / invalid : chars",
        date_text="March 03, 2021",
        download_url="/file.pdf",
        year_code="y2",
        year_label="2010-2011",
        report_code=None,
        type_code=None,
        is_active=None,
    )
    target = report.target_path(tmp_path)
    assert target.parent.name == "2010-2011"
    assert target.name.startswith("0003_Report_with_invalid_chars")
    assert target.suffix == ".pdf"


def test_sanitize_helpers() -> None:
    assert sanitize_filename(" report?.pdf ") == "report.pdf"
    assert sanitize_directory_name(" /Year *") == "Year"
