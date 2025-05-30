import pytest


def pytest_addoption(parser):
    parser.addoption(
        "--crawl",
        action="store_true",
        default=False,
        help="run slow loc.gov crawling test of Avram schema generation",
    )


def pytest_runtest_setup(item):
    if "crawl" in item.keywords and not item.config.getoption("--crawl"):
        pytest.skip("skipping slow crawling test, run with --crawl")
