from pathlib import Path
from astral import LocationInfo
import pytest


TESTS = Path("tests")
FIXTURES = TESTS / "fixtures"


@pytest.fixture
def pittsburgh_location_spec():
    return LocationInfo(
        "Pittsburgh", "PA", "America/New_York", 40.44127718642986, -80.00144481122433
    )


def opening_hours_examples():
    with open(str(FIXTURES / "opening_hours.txt"), encoding="utf-8") as f:
        for line in f:
            if not line.startswith("#"):
                yield line.strip()


@pytest.fixture(params=opening_hours_examples())
def opening_hours_example(request):
    return request.param
