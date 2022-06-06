import datetime as dt

from py_opening_hours.evaluate import OpenHours
from py_opening_hours.data_structures import RuleStatus


def test_simple(pittsburgh_location_spec):
    s = "Mo-Fr 10:00-20:00; PH off"
    hours = OpenHours.from_string(s)
    loc = pittsburgh_location_spec
    # friday during open hours
    assert (
        hours.evaluate(dt.datetime(2022, 6, 3, 10, 30), loc).status is RuleStatus.open
    )
    # friday outside open hours
    assert (
        hours.evaluate(dt.datetime(2022, 6, 3, 8, 30), loc).status is RuleStatus.closed
    )
    assert (
        hours.evaluate(dt.datetime(2022, 6, 3, 20, 30), loc).status is RuleStatus.closed
    )
    # saturday (two times)
    assert (
        hours.evaluate(dt.datetime(2022, 6, 4, 10, 30), loc).status is RuleStatus.closed
    )
    assert (
        hours.evaluate(dt.datetime(2022, 6, 4, 8, 30), loc).status is RuleStatus.closed
    )
    # holidays
    # new years day
    assert (
        hours.evaluate(dt.datetime(2022, 1, 1, 10, 30), loc).status is RuleStatus.closed
    )
    assert (
        hours.evaluate(dt.datetime(2022, 1, 1, 8, 30), loc).status is RuleStatus.closed
    )
    # juneteeth (official date and observed date)
    assert (
        hours.evaluate(dt.datetime(2022, 6, 19, 10, 30), loc).status
        is RuleStatus.closed
    )
    assert (
        hours.evaluate(dt.datetime(2022, 6, 19, 8, 30), loc).status is RuleStatus.closed
    )
    assert (
        hours.evaluate(dt.datetime(2022, 6, 20, 10, 30), loc).status
        is RuleStatus.closed
    )
    assert (
        hours.evaluate(dt.datetime(2022, 6, 20, 8, 30), loc).status is RuleStatus.closed
    )


def test_sunrise_sunset(pittsburgh_location_spec):
    s = "Mo-Fr sunrise-sunset; Sa-Su 11:00-sunset; PH off"
    loc = pittsburgh_location_spec
    hours = OpenHours.from_string(s)
    # Mon during daylight
    assert (
        hours.evaluate(dt.datetime(2022, 6, 6, 10, 10), loc).status is RuleStatus.open
    )
    # Mon before sunrise (5:50 am)
    assert (
        hours.evaluate(dt.datetime(2022, 6, 6, 5, 15), loc).status is RuleStatus.closed
    )
    assert hours.evaluate(dt.datetime(2022, 6, 6, 6, 15), loc).status is RuleStatus.open
    # Mon after sunset (8:47 pm)
    assert (
        hours.evaluate(dt.datetime(2022, 6, 6, 20, 30), loc).status is RuleStatus.open
    )
    assert (
        hours.evaluate(dt.datetime(2022, 6, 6, 21, 0), loc).status is RuleStatus.closed
    )
    # Sun after sunrise, before opening
    assert (
        hours.evaluate(dt.datetime(2022, 6, 5, 10, 10), loc).status is RuleStatus.closed
    )
    # Sun during opening
    assert (
        hours.evaluate(dt.datetime(2022, 6, 5, 11, 10), loc).status is RuleStatus.open
    )
    # Holiday
    assert (
        hours.evaluate(dt.datetime(2022, 11, 24, 11, 10), loc).status
        is RuleStatus.closed
    )


def test_sunset_sunrise(pittsburgh_location_spec):
    s = 'sunset-sunrise open "Beware of vampires!"; PH off'
    hours = OpenHours.from_string(s)
    loc = pittsburgh_location_spec
    # Mon during daylight
    assert (
        hours.evaluate(dt.datetime(2022, 6, 6, 10, 10), loc).status is RuleStatus.closed
    )
    # Mon before sunrise (5:50 am)
    assert hours.evaluate(dt.datetime(2022, 6, 6, 5, 15), loc).status is RuleStatus.open
    assert (
        hours.evaluate(dt.datetime(2022, 6, 6, 6, 15), loc).status is RuleStatus.closed
    )
    # Mon after sunset (8:47 pm)
    assert (
        hours.evaluate(dt.datetime(2022, 6, 6, 20, 30), loc).status is RuleStatus.closed
    )
    assert hours.evaluate(dt.datetime(2022, 6, 6, 21, 0), loc).status is RuleStatus.open
    # Sun after sunrise
    assert (
        hours.evaluate(dt.datetime(2022, 6, 5, 10, 10), loc).status is RuleStatus.closed
    )
    # Holiday
    assert (
        hours.evaluate(dt.datetime(2022, 11, 24, 5, 10), loc).status
        is RuleStatus.closed
    )


def test_time_only():
    s = "07:00-21:00"
    hours = OpenHours.from_string(s)
    loc = None
    assert (
        hours.evaluate(dt.datetime(2022, 6, 6, 5, 0), loc).status is RuleStatus.closed
    )
    assert hours.evaluate(dt.datetime(2022, 6, 6, 10, 0), loc).status is RuleStatus.open
    assert (
        hours.evaluate(dt.datetime(2022, 6, 6, 22, 10), loc).status is RuleStatus.closed
    )
    assert hours.evaluate(dt.datetime(2022, 6, 5, 10, 0), loc).status is RuleStatus.open


def test_readme_example():
    s = "Mo-Fr 09:00-17:00; PH Off"
    hours = OpenHours.from_string(s)
    monday_at_11_am = dt.datetime(2022, 6, 6, 11, 0)
    assert hours.evaluate(monday_at_11_am).status is RuleStatus.open
