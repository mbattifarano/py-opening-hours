from py_opening_hours import data_structures as ds
import datetime as dt


def test_timespan_contains():
    interval = ds.TimeSpan(
        ds.ExtendedTime.from_time(ds.Time(8, 30)),
        ds.ExtendedTime.from_time(ds.Time(15, 45)),
        False,
        None,
    )
    date = dt.date(2022, 6, 3)
    during = dt.datetime.combine(date, dt.time(10, 0))
    before_open = dt.datetime.combine(date, dt.time(8))
    after_close = dt.datetime.combine(date, dt.time(15, 50))
    assert interval.contains(during, None) is True
    assert interval.contains(before_open, None) is False
    assert interval.contains(after_close, None) is False

    interval = ds.TimeSpan(
        ds.ExtendedTime.from_time(ds.Time(8, 30)),
        ds.ExtendedTime.from_time(ds.Time(15, 45)),
        True,
        None,
    )
    assert interval.contains(during, None) is True
    assert interval.contains(before_open, None) is False
    assert interval.contains(after_close, None) is True

    interval = ds.TimeSpan(ds.ExtendedTime.from_time(ds.Time(8, 30)), None, True, None)
    assert interval.contains(during, None) is True
    assert interval.contains(before_open, None) is False
    assert interval.contains(after_close, None) is True


def test_day_of_week():
    assert ds.DayOfWeek.Mo.tomorrow() is ds.DayOfWeek.Tu
    assert ds.DayOfWeek.Su.tomorrow() is ds.DayOfWeek.Mo

    days = list(ds.DayOfWeek.Sa.until(ds.DayOfWeek.Tu))
    assert days == [ds.DayOfWeek.Sa, ds.DayOfWeek.Su, ds.DayOfWeek.Mo, ds.DayOfWeek.Tu]
    days = list(ds.DayOfWeek.Sa.until(ds.DayOfWeek.Sa))
    assert days == [ds.DayOfWeek.Sa]

    a_friday = dt.date(2022, 6, 3)
    assert ds.DayOfWeek.from_date(a_friday) is ds.DayOfWeek.Fr


def test_weekday_span():
    ws = ds.WeekdaySpan(ds.DayOfWeek.Fr, None, (), 0)
    assert ws.contains(dt.date(2022, 6, 3)) is True
    assert ws.contains(dt.date(2022, 6, 4)) is False
    ws = ds.WeekdaySpan(ds.DayOfWeek.Fr, ds.DayOfWeek.Mo, (), 0)
    assert ws.contains(dt.date(2022, 6, 3)) is True
    assert ws.contains(dt.date(2022, 6, 4)) is True
    assert ws.contains(dt.date(2022, 6, 7)) is False
    ws = ds.WeekdaySpan(ds.DayOfWeek.Fr, None, (1, 2, -1), 0)
    assert ws.contains(dt.date(2022, 6, 3)) is True
    assert ws.contains(dt.date(2022, 6, 4)) is False
    assert ws.contains(dt.date(2022, 6, 10)) is True
    assert ws.contains(dt.date(2022, 6, 17)) is False
    assert ws.contains(dt.date(2022, 6, 24)) is True
    ws = ds.WeekdaySpan(ds.DayOfWeek.Su, None, (-1,), 2)
    assert ws.contains(dt.date(2022, 6, 28)) is True
    assert ws.contains(dt.date(2022, 6, 26)) is False
    ws = ds.WeekdaySpan(ds.DayOfWeek.Th, None, (1,), -2)
    assert ws.contains(dt.date(2022, 5, 31)) is True
