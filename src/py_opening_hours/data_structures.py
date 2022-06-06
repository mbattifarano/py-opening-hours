from typing import Iterable, NamedTuple, List, Tuple
from enum import Enum
import datetime as dt
from astral import LocationInfo
from astral.sun import sun
from . import datetime_utils as dt_utils
from . import settings
from .common import OpeningHoursError


TODAY = dt.date.today()


class Comment(NamedTuple):
    text: str

    @staticmethod
    def load(tokens):
        return Comment(";".join(tokens))


class PlusOrMinus(Enum):
    plus = "+"
    minus = "-"

    @staticmethod
    def load(tokens):
        return PlusOrMinus(tokens[0])

    def modify(self, n: int) -> int:
        if self is PlusOrMinus.minus:
            return -n
        return n


class Event(Enum):
    dawn = 1
    sunrise = 2
    sunset = 3
    dusk = 4

    @staticmethod
    def load(tokens):
        return Event[tokens[0]]

    def to_datetime(self, date: dt.date, loc: LocationInfo) -> dt.datetime:
        if loc is None:
            raise OpeningHoursError(
                f"Relative time {self.name} encountered, please specify location."
            )
        return sun(loc.observer, date=date, tzinfo=loc.timezone)[self.name]

    def to_time(self, date: dt.date, loc: LocationInfo) -> dt.time:
        return self.to_datetime(date, loc).time()


class Time(NamedTuple):
    hour: int
    minute: int

    @staticmethod
    def load(tokens):
        h = int(tokens.get("hh", 0))
        m = int(tokens.get("mm", 0))
        return Time(h, m)

    def to_time(self) -> dt.time:
        return dt.time(self.hour, self.minute, 0)


class VariableTime(NamedTuple):
    event: Event
    plus_or_minus: PlusOrMinus = PlusOrMinus.plus
    time: Time = Time(0, 0)

    @staticmethod
    def load(tokens):
        try:
            event, pm, time = tokens
            return VariableTime(event, pm, time)
        except ValueError:
            (event,) = tokens
            return VariableTime(event)

    def to_time(self, date: dt.date, loc: LocationInfo) -> dt.time:
        t = self.event.to_datetime(date, loc)
        offset = dt.timedelta(hours=self.time.hour, minutes=self.time.minute)
        return {
            PlusOrMinus.plus: (t + offset).time(),
            PlusOrMinus.minus: (t - offset).time(),
        }[self.plus_or_minus]


class ExtendedTime(NamedTuple):
    time: Time
    vtime: VariableTime

    @staticmethod
    def from_time(t: Time):
        return ExtendedTime(t, None)

    @staticmethod
    def from_variable_time(t: VariableTime):
        return ExtendedTime(None, t)

    @staticmethod
    def load(tokens):
        (t,) = tokens
        if isinstance(t, Time):
            return ExtendedTime.from_time(t)
        if isinstance(t, VariableTime):
            return ExtendedTime.from_variable_time(t)
        raise OpeningHoursError(f"Unrecognized type for extended time: {type(t)}")

    def to_time(self, date: dt.date, loc: LocationInfo) -> dt.time:
        if self.time is not None:
            return self.time.to_time()
        if self.vtime is not None:
            return self.vtime.to_time(date, loc)
        raise OpeningHoursError("One of `time`, `vtime` should be not None.")


class TimeSpan(NamedTuple):
    start: ExtendedTime
    end: ExtendedTime
    open_end: bool
    every: Time

    @staticmethod
    def load(tokens):
        data = tokens.as_dict()
        start_time = unpack(data.get("start_time"))
        end_time = unpack(data.get("end_time"))
        open_end = "open_end" in data
        every = unpack(data.get("every"))
        return TimeSpan(start_time, end_time, open_end, every)

    def to_time_interval(self, date, loc):
        return self.start.to_time(date, loc), self.end.to_time(date, loc)

    def contains(self, datetime: dt.datetime, loc: LocationInfo) -> bool:
        date = datetime.date()
        time = datetime.time()
        start = self.start.to_time(date, loc)
        after_open = time >= start
        if self.open_end:
            return after_open
        end = self.end.to_time(date, loc)
        before_end = time <= end
        if start <= end:
            return after_open and before_end
        # if end < start (e.g. 9pm-5am) we want either
        # time >= start (e.g. 10pm) OR
        # time <= end (e.g. 4am)
        return after_open or before_end


class DayOfWeek(Enum):
    Mo = 0
    Tu = 1
    We = 2
    Th = 3
    Fr = 4
    Sa = 5
    Su = 6

    @staticmethod
    def load(tokens):
        return DayOfWeek[tokens[0]]

    @staticmethod
    def from_date(date: dt.date):
        return DayOfWeek(date.weekday())

    def tomorrow(self) -> "DayOfWeek":
        return DayOfWeek((self.value + 1) % 7)

    def until(self, other: "DayOfWeek") -> Iterable["DayOfWeek"]:
        day = self
        while day is not other:
            yield day
            day = day.tomorrow()
        yield day


class WeekdaySpan(NamedTuple):
    start: DayOfWeek
    end: DayOfWeek
    every: Tuple[int]
    offset: int

    @staticmethod
    def load(tokens):
        data = tokens.as_dict()
        start = data["start"]
        end = data.get("end")
        every = tuple(data.get("every", []))
        offset = data.get("offset", 0)
        return WeekdaySpan(start, end, every, offset)

    def _contains_range(self, date: dt.date) -> bool:
        wday = DayOfWeek.from_date(date)
        for day in self.start.until(self.end):
            if day is wday:
                return True
        return False

    def _contains_every(self, date: dt.date):
        offset = dt.timedelta(days=self.offset)
        offset_date = date - offset
        if DayOfWeek.from_date(offset_date) is not self.start:
            return False
        days = list(dt_utils.weekdays_in_month(offset_date))
        for n in self.every:
            if offset_date == (days[n - 1 if n > 0 else n]):
                return True
        return False

    def contains(self, date: dt.date) -> bool:
        if self.end is not None:
            return self._contains_range(date)
        if self.every:
            return self._contains_every(date)
        return self.start is DayOfWeek.from_date(date)


class Month(Enum):
    Jan = 1
    Feb = 2
    Mar = 3
    Apr = 4
    May = 5
    Jun = 6
    Jul = 7
    Aug = 8
    Sep = 9
    Oct = 10
    Nov = 11
    Dec = 12

    @staticmethod
    def load(tokens):
        return Month[tokens[0]]


class SpecialDate(Enum):
    easter = 1

    def contains(self, date: dt.date) -> bool:
        return dt_utils.is_easter(date)


class Date(NamedTuple):
    year: int
    month: Month
    day: int
    special: SpecialDate = None

    @staticmethod
    def load(tokens):
        data = tokens.as_dict()
        year = data.get("year")
        month = data.get("month")
        day = data.get("daynum")
        special = data.get("special")
        return Date(year, month, day, special)

    def contains(self, date: dt.date) -> bool:
        if self.special is not None:
            return self.special.contains(date)
        return date == dt.date(self.year, self.month.value, self.day)


class HolidayType(Enum):
    public = "PH"
    school = "SH"

    @staticmethod
    def load(tokens):
        return HolidayType(tokens[0])


class Holiday(NamedTuple):
    type: HolidayType
    day_offset: int

    @staticmethod
    def load(tokens):
        htype = tokens[0]
        try:
            ndays = tokens[1]
        except IndexError:
            ndays = 0
        return Holiday(htype, ndays)

    def contains(self, date: dt.date) -> bool:
        offset_date = date - dt.timedelta(days=self.day_offset)
        return offset_date in dt_utils.get_holidays(settings.COUNTRY, settings.STATE)


class DateOffset(NamedTuple):
    ndays: int
    direction: PlusOrMinus
    day: DayOfWeek

    @staticmethod
    def load(tokens):
        data = tokens.as_dict()
        ndays = data.get("ndays")
        direction = data.get("pm")
        day = data.get("wday")
        return DateOffset(ndays, direction, day)


class WeekdaySelector(NamedTuple):
    weekdays: List[WeekdaySpan]
    holidays: List[Holiday]

    @staticmethod
    def load(tokens):
        data = tokens.as_dict()
        return WeekdaySelector(data.get("weekday_ranges"), data.get("holidays"))

    def contains(self, date: dt.date) -> bool:
        return any(ws.contains(date) for ws in self.weekdays or []) or any(
            hs.contains(date) for hs in self.holidays or []
        )


class WeekSpan(NamedTuple):
    start: int
    end: int = None
    every: int = None

    @staticmethod
    def load(tokens):
        return WeekSpan(*tokens)

    def contains(self, date: dt.date) -> bool:
        _, weeknum, _ = date.isocalendar()
        return (
            (weeknum >= self.start)
            and (self.end is None or weeknum <= self.end)
            and (self.every is None or ((weeknum - self.start) % self.every == 0))
        )


class MonthdaySpan(NamedTuple):
    start: Date
    start_offset: DateOffset
    end: Date
    end_offset: DateOffset
    open_end: bool

    @staticmethod
    def load_from_dates(tokens):
        data = tokens.as_dict()
        start = unpack(data["start_date"])
        start_offset = data.get("start_offset")
        open_end = "open_end" in data
        end = data.get("end_date")
        end_offset = data.get("end_offset")
        return MonthdaySpan(start, start_offset, end, end_offset, open_end)

    @staticmethod
    def load_from_year_months(tokens):
        data = tokens.as_dict()
        start = Date(data.get("year"), data["start_month"], None)
        if "end_month" in data:
            end = Date(data.get("year"), data["end_month"], None)
        else:
            end = start
        return MonthdaySpan(start, None, end, None, False)

    def contains(self, date: dt.date):
        raise NotImplementedError


class YearSpan(NamedTuple):
    start: int
    end: int
    open_end: bool
    every: int

    @staticmethod
    def load(tokens):
        data = tokens.as_dict()
        start = int(data["start_year"])
        explicit_open_end = "open_end" in data
        explicit_end = "end_year" in data
        every = data.get("every")
        if every and not explicit_end:
            # "2022/2" should be read as every 2 years starting in 2022
            # In this case open_end should be True even though it was
            # not explicitly denoted
            # ex "2020+" == "2020/1"
            open_end = True
        else:
            open_end = explicit_open_end
        if open_end:
            end = None
        else:
            end = data.get("end_year", start)
        return YearSpan(start, end, open_end, every)

    def contains(self, date: dt.date) -> bool:
        return (
            (date.year >= self.start)
            and (self.open_end or (date.year <= self.end))
            and (self.every is None or ((date.year - self.start) % self.every == 0))
        )


class TimeSelector(NamedTuple):
    always: bool
    comment: Comment
    years: YearSpan
    monthdays: MonthdaySpan
    weeks: List[WeekSpan]
    weekdays: WeekdaySelector
    times: List[TimeSpan]

    @staticmethod
    def load(tokens):
        data = tokens.as_dict()
        always = "always" in data
        comment = data.get("comment")
        years = data.get("years")
        monthdays = unpack(data.get("monthdays"))
        weeks = data.get("weeks")
        weekdays = data.get("weekdays")
        times = data.get("times")
        return TimeSelector(always, comment, years, monthdays, weeks, weekdays, times)

    def contains(self, datetime: dt.datetime, loc: LocationInfo) -> bool:
        if self.always:
            return True
        date = datetime.date()
        return (
            (self.years is None or self.years.contains(date))
            and (self.monthdays is None or self.monthdays.contains(date))
            and (self.weeks is None or any((ws.contains(date) for ws in self.weeks)))
            and (self.weekdays is None or self.weekdays.contains(date))
            and (
                self.times is None
                or any(ts.contains(datetime, loc) for ts in self.times)
            )
        )


class RuleStatus(Enum):
    unknown = 0
    open = 1
    closed = 2
    off = 2

    @staticmethod
    def load(tokens):
        return RuleStatus[tokens[0]]


class RuleModifier(NamedTuple):
    status: RuleStatus
    comment: Comment

    @staticmethod
    def load(tokens):
        data = tokens.as_dict()
        status = data.get("status", RuleStatus.open)
        comment = unpack(data.get("comment"))
        return RuleModifier(status, comment)


class Rule(NamedTuple):
    time_selector: TimeSelector
    modifier: RuleModifier

    @staticmethod
    def load(tokens):
        selector = tokens[0]
        try:
            modifier = tokens[1]
        except IndexError:
            modifier = None
        return Rule(selector, modifier)

    def contains(self, datetime: dt.datetime, loc: LocationInfo) -> bool:
        return self.time_selector.contains(datetime, loc)


def unpack(singleton: List):
    if singleton is not None:
        return singleton[0]
    return None
