"""pyparsing implementation of the opening hours syntax

https://wiki.openstreetmap.org/wiki/Key:opening_hours/specification
"""
from typing import Iterable, List
import pyparsing as pp
from . import data_structures as ds

comma = pp.Literal(",")

ppc = pp.pyparsing_common


def as_two_digit_string(num: int) -> str:
    return f"{num:02d}"


def integers(start: int, stop: int) -> Iterable[int]:
    """Inclusive range"""
    return list(range(start, stop + 1))


def process_range(tokens):
    data = tokens.as_dict()
    start = data["range_start"]
    end = data.get("range_end")
    if end is not None:
        return (int(start), int(end))
    return int(start)


# basic elements
space = pp.Literal(" ")
comment_delimiter = pp.Literal('"')
comment_words = pp.Word(pp.printables + " ", exclude_chars='"')
comment = (
    pp.Suppress(comment_delimiter)
    + pp.Opt(comment_words).set_parse_action(ds.Comment.load)
    + pp.Suppress(comment_delimiter)
).set_results_name("comment")
postive_number = pp.Word(pp.nums).set_parse_action(ppc.convert_to_integer)
year = (
    pp.Word(pp.nums, exact=4)
    .set_parse_action(ppc.convert_to_integer)
    .set_results_name("year")
)
month = (
    pp.one_of(
        [
            "Jan",
            "Feb",
            "Mar",
            "Apr",
            "May",
            "Jun",
            "Jul",
            "Aug",
            "Sep",
            "Oct",
            "Nov",
            "Dec",
        ],
    )
    .set_parse_action(ds.Month.load)
    .set_results_name("month")
)
two_digit_number = pp.Word(pp.nums, min=1, max=2).set_parse_action(
    ppc.convert_to_integer
)
weeknum = two_digit_number.set_results_name("weeknum")
daynum = two_digit_number.set_results_name("daynum")
wday = pp.one_of(["Su", "Mo", "Tu", "We", "Th", "Fr", "Sa"]).add_parse_action(
    ds.DayOfWeek.load
)
minute = pp.one_of(map(as_two_digit_string, integers(0, 59))).set_parse_action(
    ppc.convert_to_integer
)
hour = pp.one_of(map(as_two_digit_string, integers(0, 24))).set_parse_action(
    ppc.convert_to_integer
)
hour_minutes = (hour("hh") + pp.Suppress(":") + minute("mm")).set_parse_action(
    ds.Time.load
)
extended_hour = hour | pp.one_of(
    map(as_two_digit_string, integers(25, 48))
).set_parse_action(ppc.convert_to_integer)
extended_hour_minutes = (
    extended_hour("hh") + pp.Suppress(":") + minute("mm")
).set_parse_action(ds.Time.load)
plus_or_minus = (pp.Literal("+") | pp.Literal("-")).set_parse_action(
    ds.PlusOrMinus.load
)
range_op = pp.Suppress("-")
every_op = pp.Suppress("/")
open_end = pp.Literal("+").set_results_name("open_end")

# Year selector
year_range = (
    year("start_year")
    + pp.Opt(
        open_end
        | (every_op + postive_number("every"))
        | ((range_op + year("end_year")) + pp.Opt(every_op + postive_number("every")))
    )
).set_parse_action(ds.YearSpan.load)
year_selector = pp.delimited_list(year_range)

# Month selector
variable_date = pp.Literal("easter")
date_from = (pp.Opt(year) + month + daynum).set_parse_action(ds.Date.load) | (
    pp.Opt(year) + variable_date
).set_parse_action(ds.Date.load)
date_to = (date_from | daynum).set_parse_action(ds.Date.load)
day = pp.Literal("day") | pp.Literal("days")


def day_offset_to_integer(tokens):
    pm, n = tokens
    return -n if pm is ds.PlusOrMinus.minus else n


day_offset = (plus_or_minus + postive_number).set_parse_action(
    day_offset_to_integer
) + pp.Suppress(day)
date_offset = (
    pp.Opt((plus_or_minus("pm") + wday("wday"))) + pp.Opt(day_offset("ndays"))
).set_parse_action(ds.DateOffset.load)
monthday_range = (
    date_from.set_results_name("start_date")
    + pp.Opt(
        (pp.Opt(date_offset("start_offset")) + open_end)
        | (
            pp.Opt(date_offset("start_offset"))
            + range_op
            + date_to("end_date")
            + pp.Opt(date_offset("end_offset"))
        )
    )
).set_parse_action(ds.MonthdaySpan.load_from_dates) | (
    pp.Opt(year("year")) + month("start_month") + pp.Opt(range_op + month("end_month"))
).set_parse_action(
    ds.MonthdaySpan.load_from_year_months
)
monthday_selector = pp.delimited_list(monthday_range)

# Week selector
week = (
    weeknum + pp.Opt(range_op + weeknum + pp.Opt(every_op + postive_number))
).set_parse_action(ds.WeekSpan.load)
week_selector = pp.CaselessLiteral("week").suppress() + pp.delimited_list(week)

# Weekday selector
public_holiday = pp.Literal("PH").add_parse_action(ds.HolidayType.load)
school_holiday = pp.Literal("SH").add_parse_action(ds.HolidayType.load)
nth = pp.one_of(map(str, integers(1, 5)))
nth_entry = (
    pp.Combine("-" + nth)("range_start")
    | (nth("range_start") + pp.Opt(pp.Suppress("-") + nth("range_end")))
).set_parse_action(process_range)
holiday = ((public_holiday + pp.Opt(day_offset)) | school_holiday).set_parse_action(
    ds.Holiday.load
)
holiday_sequence = pp.delimited_list(holiday).set_results_name("holidays")
weekday_range = (
    wday("start")
    + pp.Opt(
        (range_op + wday("end"))
        | (
            pp.Suppress("[")
            + pp.delimited_list(nth_entry).set_results_name("every")
            + pp.Suppress("]")
            + pp.Opt(day_offset("offset"))
        )
    )
).add_parse_action(ds.WeekdaySpan.load)
weekday_seqeunce = pp.delimited_list(weekday_range).set_results_name("weekday_ranges")
weekday_selector = (
    (holiday_sequence + pp.Opt(comma) + weekday_seqeunce)
    | (weekday_seqeunce + pp.Opt(comma + holiday_sequence))
    | holiday_sequence
).set_parse_action(ds.WeekdaySelector.load)

# Time selector
event = (
    pp.one_of(["dawn", "sunrise", "sunset", "dusk"])
    .set_results_name("event")
    .set_parse_action(ds.Event.load)
)
variable_time = (
    event | (pp.Suppress("(") + event + plus_or_minus + hour_minutes + pp.Suppress(")"))
).set_parse_action(ds.VariableTime.load)
extended_time = extended_hour_minutes | variable_time
time = (hour_minutes | variable_time).set_parse_action(ds.ExtendedTime.load)
timespan = (
    (time | time).set_results_name(
        "start_time"
    )  # this is a hack to get avoid `{'start_time': None}`
    + pp.Opt(
        pp.Literal("+").set_results_name("open_end")
        | (
            range_op
            + (time | time).set_results_name("end_time")
            + pp.Opt(
                pp.Literal("+").set_results_name("open_end")
                | (
                    pp.Suppress("/")
                    + (
                        hour_minutes
                        | postive_number("mm").set_parse_action(ds.Time.load)
                    ).set_results_name("every")
                )
            )
        )
    )
).set_parse_action(ds.TimeSpan.load)
time_selector = pp.delimited_list(timespan).set_results_name("time_selector")

# Selectors
seperator_for_readability = pp.Literal(":")
small_range_selectors = pp.Opt(weekday_selector).set_results_name("weekdays") + pp.Opt(
    time_selector
).set_results_name("times")
wide_range_selectors = (comment + ":") | (
    pp.Opt(year_selector("years"))
    + pp.Opt(monthday_selector("monthdays"))
    + pp.Opt(week_selector("weeks"))
    + pp.Opt(seperator_for_readability)
)
always = pp.Literal("24/7").set_results_name("always")
selector_sequence = (
    always | (wide_range_selectors + small_range_selectors)
).set_parse_action(ds.TimeSelector.load)

# Rule modifiers
status = (
    pp.one_of(["open", "closed", "off", "unknown"])
    .set_results_name("status")
    .add_parse_action(ds.RuleStatus.load)
)
rule_modifier = ((status + pp.Opt(comment)) | comment | pp.empty).set_parse_action(
    ds.RuleModifier.load
)

# Rule separators
fallback_rule_separator = pp.Literal("||")
additional_rule_separator = pp.Literal(",")
normal_rule_separator = pp.Literal(";")
any_rule_separator = (
    normal_rule_separator | additional_rule_separator | fallback_rule_separator
)

# Time domain
rule_sequence = selector_sequence + rule_modifier
time_domain = pp.delimited_list(
    rule_sequence.set_parse_action(ds.Rule.load),
    delim=any_rule_separator,
).set_results_name("rules")


def parse(s: str) -> List[ds.Rule]:
    return time_domain.parse_string(s).rules
