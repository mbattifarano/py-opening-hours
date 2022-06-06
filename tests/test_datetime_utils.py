from py_opening_hours import datetime_utils as dt_utils
import datetime as dt


def test_nth_weekday_of_month():
    date = dt.date(2022, 6, 3)
    assert dt_utils.first_weekday_in_month(date) == date
    assert dt_utils.as_nth_weekday_of_month(date) == 1

    date = dt.date(2022, 6, 10)
    assert dt_utils.as_nth_weekday_of_month(date) == 2


def test_weekdays_in_month():
    date = dt.date(2022, 6, 10)
    days = list(dt_utils.weekdays_in_month(date))
    assert len(days) == 4
    assert days == [
        date.replace(day=3),
        date,
        date.replace(day=17),
        date.replace(day=24),
    ]
