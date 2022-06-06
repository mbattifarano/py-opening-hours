import datetime as dt
import calendar
from typing import Iterable
import holidays
from dateutil.easter import easter


def first_weekday_in_month(date: dt.date) -> dt.date:
    """The date of the first weekday in the month

    The weekday and month are both taken from date.
    For example, this function maps 2022-06-10 (a friday) to
    2022-06-03, the first friday of June 2022.

    Modified from: https://stackoverflow.com/a/71688384
    """
    first = date.replace(day=1)
    days = (date.weekday() - first.weekday()) % 7
    return date.replace(day=first.day + days)


def as_nth_weekday_of_month(date: dt.date) -> int:
    first = first_weekday_in_month(date)
    return ((date.day - first.day) // 7) + 1


def weekdays_in_month(date: dt.date) -> Iterable[dt.date]:
    first = first_weekday_in_month(date)
    _, ndays = calendar.monthrange(date.year, date.month)
    day = first.day
    while day <= ndays:
        yield first.replace(day=day)
        day += 7


HOLIDAYS = {}


def get_holidays(country, state):
    try:
        return HOLIDAYS[(country, state)]
    except KeyError:
        res = holidays.country_holidays(country, state=state)
        HOLIDAYS[(country, state)] = res
        return res


def is_easter(date: dt.date) -> bool:
    return date == easter(date.year)
