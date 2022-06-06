import pytest
from py_opening_hours import syntax, data_structures as ds
from pyparsing.exceptions import ParseException


def test_year():
    res = syntax.year.parse_string("1984")
    assert len(res) == 1
    assert res[0] == 1984

    with pytest.raises(ParseException):
        syntax.year.parse_string("21")

    with pytest.raises(ParseException):
        syntax.year.parse_string("foo")


def test_comment():
    s = '"this is a comment"'
    res = syntax.comment.parse_string(s)
    assert len(res) == 1
    comment = res[0]
    assert isinstance(comment, ds.Comment)
    assert comment.text == "this is a comment"


def test_timespan():
    s = "10:00-20:00/45"
    res = syntax.timespan.parse_string(s)
    assert len(res) == 1
    ts = res[0]
    assert isinstance(ts, ds.TimeSpan)
    assert ts.start.time == (10, 0)
    assert ts.end.time == (20, 0)
    assert ts.open_end is False
    assert ts.every == (0, 45)


def test_weekdayspan():
    s = "Mo-Fr"
    res = syntax.weekday_range.parse_string(s)
    assert len(res) == 1
    ws = res[0]
    assert isinstance(ws, ds.WeekdaySpan)
    assert ws.start is ds.DayOfWeek.Mo
    assert ws.end is ds.DayOfWeek.Fr

    s = "Mo[1, -1]"
    res = syntax.weekday_range.parse_string(s)
    assert len(res) == 1
    ws = res[0]
    assert isinstance(ws, ds.WeekdaySpan)
    assert ws.start is ds.DayOfWeek.Mo
    assert ws.end is None
    assert ws.every == (1, -1)

    s = "Mo[1-3]"
    res = syntax.weekday_range.parse_string(s)
    assert len(res) == 1
    ws = res[0]
    assert isinstance(ws, ds.WeekdaySpan)
    assert ws.start is ds.DayOfWeek.Mo
    assert ws.end is None
    assert ws.every == ((1, 3),)


def test_public_holidays():
    s = "PH"
    res = syntax.weekday_selector.parse_string(s)
    ws = res[0]
    assert ws.weekdays is None
    assert ws.holidays == [ds.Holiday(ds.HolidayType.public, 0)]


def test_yearspan():
    s = "2022"
    res = syntax.year_selector.parse_string(s)
    assert len(res) == 1
    ys = res[0]
    assert isinstance(ys, ds.YearSpan)
    assert ys.start == 2022
    assert ys.end == 2022
    assert ys.every is None
    assert ys.open_end is False

    s = "2022+"
    res = syntax.year_selector.parse_string(s)
    assert len(res) == 1
    ys = res[0]
    assert isinstance(ys, ds.YearSpan)
    assert ys.start == 2022
    assert ys.end is None
    assert ys.every is None
    assert ys.open_end is True

    s = "2020-2030/2"
    res = syntax.year_selector.parse_string(s)
    assert len(res) == 1
    ys = res[0]
    assert isinstance(ys, ds.YearSpan)
    assert ys.start == 2020
    assert ys.end == 2030
    assert ys.every == 2
    assert ys.open_end is False


def test_shortrange():
    s = "Mo-Fr 10:00-20:00"
    res = syntax.selector_sequence.parse_string(s)
    assert len(res) == 1
    rule = res[0]
    assert isinstance(rule, ds.TimeSelector)
    assert rule.always is False
    assert rule.weekdays == ds.WeekdaySelector(
        [ds.WeekdaySpan(ds.DayOfWeek.Mo, ds.DayOfWeek.Fr, (), 0)], None
    )
    assert rule.times == [
        ds.TimeSpan(
            ds.ExtendedTime.from_time(ds.Time(10, 0)),
            ds.ExtendedTime.from_time(ds.Time(20, 0)),
            False,
            None,
        )
    ]


def test_always_rule():
    s = '24/7 closed "always closed"'
    res = syntax.time_domain.parse_string(s)
    rules = res.rules
    assert len(rules) == 1
    rule = rules[0]
    assert isinstance(rule, ds.Rule)
    ts = rule.time_selector
    assert isinstance(ts, ds.TimeSelector)
    assert ts == ds.TimeSelector(True, None, None, None, None, None, None)
    rm = rule.modifier
    assert isinstance(rm, ds.RuleModifier)
    assert rm == ds.RuleModifier(ds.RuleStatus.closed, ds.Comment("always closed"))


def test_years_rule():
    s = "2013,2015,2050-2053,2055/2,2020-2029/3,2060+ Jan 1"
    res = syntax.time_domain.parse_string(s)
    rules = res.rules
    assert len(rules) == 1
    rule = rules[0]
    assert rule.modifier == ds.RuleModifier(ds.RuleStatus.open, None)
    ts = rule.time_selector
    assert ts.always is False
    assert ts.comment is None
    assert ts.weekdays is None
    assert ts.times is None
    assert len(ts.years) == 6
    assert ts.years[0] == ds.YearSpan(2013, 2013, False, None)
    assert ts.years[2] == ds.YearSpan(2050, 2053, False, None)
    assert ts.years[3] == ds.YearSpan(2055, None, True, 2)
    assert ts.years[4] == ds.YearSpan(2020, 2029, False, 3)
    assert ts.years[5] == ds.YearSpan(2060, None, True, None)
    assert ts.monthdays == ds.MonthdaySpan(
        ds.Date(None, ds.Month.Jan, 1), None, None, None, False
    )


def test_regular_hours_holidays_off():
    s = "Mo-Fr 10:00-20:00; PH off"
    res = syntax.time_domain.parse_string(s)
    rules = res.rules
    regular_hours = rules[0]
    ts = regular_hours.time_selector
    assert ts.always is False
    assert ts.weekdays == ds.WeekdaySelector(
        [ds.WeekdaySpan(ds.DayOfWeek.Mo, ds.DayOfWeek.Fr, (), 0)], None
    )
    assert ts.times == [
        ds.TimeSpan(
            ds.ExtendedTime.from_time(ds.Time(10, 0)),
            ds.ExtendedTime.from_time(ds.Time(20, 0)),
            False,
            None,
        )
    ]
    assert regular_hours.modifier == ds.RuleModifier(ds.RuleStatus.open, None)
    holiday_hours = rules[1]
    assert holiday_hours.time_selector.weekdays == ds.WeekdaySelector(
        None, [ds.Holiday(ds.HolidayType.public, 0)]
    )
    assert holiday_hours.modifier == ds.RuleModifier(ds.RuleStatus.closed, None)


def test_holidays_off():
    s = "PH off"
    res = syntax.time_domain.parse_string(s)
    rules = res.rules
    regular_hours = rules[0]
    ts = regular_hours.time_selector
    assert ts.always is False
    assert ts.weekdays == ds.WeekdaySelector(
        weekdays=None, holidays=[ds.Holiday(ds.HolidayType.public, 0)]
    )
    assert regular_hours.modifier == ds.RuleModifier(ds.RuleStatus.off, None)


def test_per_day_schedule():
    s = "Mo 10:00-12:00,12:30-15:00; Tu-Fr 08:00-12:00,12:30-15:00; Sa 08:00-12:00"
    res = syntax.time_domain.parse_string(s)
    rules = res.rules
    assert len(rules) == 3
    monday = rules[0]
    assert monday.modifier == ds.RuleModifier(ds.RuleStatus.open, None)
    assert monday.time_selector.weekdays == ds.WeekdaySelector(
        weekdays=[ds.WeekdaySpan(ds.DayOfWeek.Mo, None, (), 0)],
        holidays=None,
    )
    assert monday.time_selector.times == [
        ds.TimeSpan(
            ds.ExtendedTime.from_time(ds.Time(10, 0)),
            ds.ExtendedTime.from_time(ds.Time(12, 0)),
            False,
            None,
        ),
        ds.TimeSpan(
            ds.ExtendedTime.from_time(ds.Time(12, 30)),
            ds.ExtendedTime.from_time(ds.Time(15, 0)),
            False,
            None,
        ),
    ]
    tu_fr = rules[1]
    assert tu_fr.modifier == ds.RuleModifier(ds.RuleStatus.open, None)
    assert tu_fr.time_selector.weekdays == ds.WeekdaySelector(
        weekdays=[ds.WeekdaySpan(ds.DayOfWeek.Tu, ds.DayOfWeek.Fr, (), 0)],
        holidays=None,
    )
    assert tu_fr.time_selector.times == [
        ds.TimeSpan(
            ds.ExtendedTime.from_time(ds.Time(8, 0)),
            ds.ExtendedTime.from_time(ds.Time(12, 0)),
            False,
            None,
        ),
        ds.TimeSpan(
            ds.ExtendedTime.from_time(ds.Time(12, 30)),
            ds.ExtendedTime.from_time(ds.Time(15, 0)),
            False,
            None,
        ),
    ]
    saturday = rules[2]
    assert saturday.modifier == ds.RuleModifier(ds.RuleStatus.open, None)
    assert saturday.time_selector.weekdays == ds.WeekdaySelector(
        weekdays=[ds.WeekdaySpan(ds.DayOfWeek.Sa, None, (), 0)],
        holidays=None,
    )
    assert saturday.time_selector.times == [
        ds.TimeSpan(
            ds.ExtendedTime.from_time(ds.Time(8, 0)),
            ds.ExtendedTime.from_time(ds.Time(12, 0)),
            False,
            None,
        ),
    ]


def test_complicated():
    s = "Mo,Tu,Th,Fr 12:00-18:00; Sa,PH 12:00-17:00; Th[3],Th[-1] off"
    res = syntax.time_domain.parse_string(s)
    rules = res.rules
    assert len(rules) == 3
    weekdays = rules[0]
    assert weekdays.time_selector.weekdays == ds.WeekdaySelector(
        [
            ds.WeekdaySpan(ds.DayOfWeek.Mo, None, (), 0),
            ds.WeekdaySpan(ds.DayOfWeek.Tu, None, (), 0),
            ds.WeekdaySpan(ds.DayOfWeek.Th, None, (), 0),
            ds.WeekdaySpan(ds.DayOfWeek.Fr, None, (), 0),
        ],
        holidays=None,
    )
    assert weekdays.time_selector.times == [
        ds.TimeSpan(
            ds.ExtendedTime.from_time(ds.Time(12, 0)),
            ds.ExtendedTime.from_time(ds.Time(18, 0)),
            False,
            None,
        )
    ]
    assert weekdays.modifier.status is ds.RuleStatus.open
    sa_holidays = rules[1]
    assert sa_holidays.time_selector.weekdays == ds.WeekdaySelector(
        weekdays=[ds.WeekdaySpan(ds.DayOfWeek.Sa, None, (), 0)],
        holidays=[ds.Holiday(ds.HolidayType.public, 0)],
    )
    assert sa_holidays.time_selector.times == [
        ds.TimeSpan(
            ds.ExtendedTime.from_time(ds.Time(12, 0)),
            ds.ExtendedTime.from_time(ds.Time(17, 0)),
            False,
            None,
        )
    ]
    assert sa_holidays.modifier.status is ds.RuleStatus.open
    thursdays = rules[2]
    assert thursdays.time_selector.weekdays == ds.WeekdaySelector(
        [
            ds.WeekdaySpan(ds.DayOfWeek.Th, None, (3,), 0),
            ds.WeekdaySpan(ds.DayOfWeek.Th, None, (-1,), 0),
        ],
        None,
    )
    assert thursdays.time_selector.times is None
    assert thursdays.modifier.status is ds.RuleStatus.closed


def test_weeks():
    s = "Feb week 06 Mo-Su 00:00-24:00; PH off"
    res = syntax.time_domain.parse_string(s)
    rules = res.rules
    assert len(rules) == 2
    feb, ph = rules
    assert feb.modifier.status is ds.RuleStatus.open
    assert feb.time_selector.monthdays == ds.MonthdaySpan(
        ds.Date(None, ds.Month.Feb, None),
        None,
        ds.Date(None, ds.Month.Feb, None),
        None,
        False,
    )
    assert feb.time_selector.weeks == [ds.WeekSpan(6, None, None)]
    assert feb.time_selector.weekdays == ds.WeekdaySelector(
        [ds.WeekdaySpan(ds.DayOfWeek.Mo, ds.DayOfWeek.Su, (), 0)], None
    )
    assert feb.time_selector.times == [
        ds.TimeSpan(
            ds.ExtendedTime.from_time(ds.Time(0, 0)),
            ds.ExtendedTime.from_time(ds.Time(24, 0)),
            False,
            None,
        )
    ]
    assert feb.modifier.status is ds.RuleStatus.open

    assert ph.time_selector.weekdays == ds.WeekdaySelector(
        None, [ds.Holiday(ds.HolidayType.public, 0)]
    )
    assert ph.modifier.status is ds.RuleStatus.closed


def test_open_with_comment():
    s = 'Mo-Sa 10:00+ "closing time not specified"'
    rules = syntax.parse(s)
    assert len(rules) == 1
    rule = rules[0]
    assert rule.time_selector.weekdays == ds.WeekdaySelector(
        [ds.WeekdaySpan(ds.DayOfWeek.Mo, ds.DayOfWeek.Sa, (), 0)], None
    )
    assert rule.time_selector.times == [
        ds.TimeSpan(ds.ExtendedTime.from_time(ds.Time(10, 0)), None, True, None)
    ]
    assert rule.modifier.comment == ds.Comment("closing time not specified")


def test_relative_times():
    s = "sunrise-sunset"
    rules = syntax.parse(s)
    assert len(rules) == 1
    rule = rules[0]
    ts = rule.time_selector
    assert ts.times[0] == ds.TimeSpan(
        ds.ExtendedTime(None, ds.VariableTime(ds.Event.sunrise)),
        ds.ExtendedTime(None, ds.VariableTime(ds.Event.sunset)),
        False,
        None,
    )


def test_example(opening_hours_example):
    rules = syntax.parse(opening_hours_example)
    assert rules
