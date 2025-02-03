"Configure pytest html reports"

import csv
import os
import sys
from collections.abc import Generator
from datetime import datetime
from pprint import pformat
from typing import Any
import pytest


def pytest_collection_modifyitems(items):
    """
    Prioritize tests based on markers.

    Args:
        items: A list of pytest.Item objects representing the collected tests.
    """

    def get_marker_order(item):
        """
        Returns the order of the marker if it exists, otherwise returns 0.
        """
        marker = item.get_closest_marker("order")
        if marker:
            try:
                return int(
                    marker.args[0]
                )  # Assuming the order is provided as an integer argument to the marker
            except (IndexError, ValueError):
                raise ValueError(  # noqa: B904
                    "Invalid order value for marker 'order'. Expected an integer."
                )
        return 0

    items.sort(key=get_marker_order)


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item: Any, call: Any) -> Generator[None, None, None]:
    """
    Hook to customize the test report, capturing the configuration
    and db state for detailed output, especially for failed tests.

    Args:
        item: The test item being reported on.
        call: The test call details.

    Yields:
        None
    """
    outcome = yield
    report = outcome.get_result()  # pyright: ignore[reportAttributeAccessIssue]

    # Get the relevant config and db information
    config = item.funcargs.get("test_config")
    db = item.funcargs.get("enginemodel_db") or item.funcargs.get(
        "elixirdb_statements"
    )

    if db:
        report.config = db.db.model_dump(exclude_unset=True)
        report.test_type = "db.base"
        report.statevars = db.statevars
    elif config:
        report.config = config["config"]
        report.test_type = config["test"]
    else:
        report.config = "Unknown"
        report.test_type = "Unknown"

    if report.when == "call" and report.failed:
        formatted_config = pformat(report.config)
        sys.stdout.write("\n=== Configuration for Failed Test ===\n")
        sys.stdout.write(f"Test: {item.nodeid}\n")
        sys.stdout.write(f"Configuration:\n{formatted_config}\n")
        sys.stdout.write("====================================\n")

        # Store failure data for CSV output
        failure_data_entry = {
            "test_name": item.nodeid,
            "test_type": report.test_type,
            "statevars": (
                report.statevars if hasattr(report, "statevars") else "N/A"
            ),
            "config": formatted_config,
        }

        if hasattr(item.session, "failure_data"):
            item.session.failure_data.append(failure_data_entry)
        else:
            item.session.failure_data = [failure_data_entry]


def pytest_sessionfinish(session: Any, exitstatus: int) -> None:
    """
    Hook to output a CSV file containing test failure data at the end of
        the test session.

    Args:
        session: The pytest session object.
        exitstatus: The exit status code of the test session.

    Returns:
        None
    """
    if hasattr(session, "failure_data") and session.failure_data:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = "tests/reports"
        os.makedirs(output_dir, exist_ok=True)
        csv_filename = os.path.join(output_dir, f"pytest_{timestamp}.csv")

        with open(csv_filename, "w", newline="", encoding="utf-8") as csvfile:
            fieldnames = [
                "test_name",
                "test_type",
                "query",
                "params",
                "statevars",
                "config",
            ]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(session.failure_data)


def pytest_html_results_table_header(cells: list[str]) -> None:
    """
    Adds custom headers to the pytest HTML report table.

    Args:
        cells: The list of cells in the header row.

    Returns:
        None
    """
    cells.insert(1, "<th>Dialect</th>")
    cells.insert(2, "<th>Test Type</th>")
    cells.insert(3, "<th>Config</th>")
    cells.insert(3, "<th>StateVars</th>")


def pytest_html_results_table_row(report: Any, cells: list[str]) -> None:
    """
    Populates the pytest HTML report rows with test information.

    Args:
        report: The test report object.
        cells: The list of cells in the current row.

    Returns:
        None
    """
    config = getattr(report, "config", "Unknown")
    test_type = getattr(report, "test_type", "Unknown")
    statevars = getattr(report, "statevars", "Unknown")
    dialect = (
        config.get("dialect", "Unknown") if isinstance(config, dict) else "Unknown"
    )

    cells.insert(1, f"<td>{dialect}</td>")
    cells.insert(2, f"<td>{test_type}</td>")
    cells.insert(3, f"<td>{config}</td>")
    cells.insert(3, f"<td>{statevars}</td>")
