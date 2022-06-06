"""Evaluate opening hours"""
import datetime as dt
from typing import Iterable, NamedTuple

from astral import LocationInfo
from .data_structures import Rule, RuleModifier, RuleStatus
from .syntax import parse


class OpenHours:
    def __init__(self, rules: Iterable[Rule]) -> None:
        self.rules = list(rules)

    @classmethod
    def from_string(cls, s: str) -> "OpenHours":
        rules = parse(s)
        return cls(rules)

    def evaluate(self, datetime: dt.datetime, loc: LocationInfo = None) -> RuleModifier:
        return evaluate(self.rules, datetime, loc)


class RuleMatch(NamedTuple):
    match: bool
    modifier: RuleModifier


def match(rule: Rule, datetime: dt.datetime, loc: LocationInfo) -> RuleMatch:
    return RuleMatch(rule.contains(datetime, loc), rule.modifier)


def evaluate(
    rules: Iterable[Rule], datetime: dt.datetime, loc: LocationInfo
) -> RuleModifier:
    """Evaluate a list of time domain rules against a datetime.

    It is assumed that the given datetime is in the localtime of
    the opening hours rules.

    This funtion will return:
        - the first matched closed rule, if one exists, or
        - the first matched open rule, if one exists, or
        - the first matched unknown rule, if one exists, or
        - closed
    Closed rules override open rules so if there are any closed rules
    matched the first match is immediately returned
    """
    matches = {}
    for rule in rules:
        is_match, modifier = match(rule, datetime, loc)
        if is_match:
            if modifier.status is RuleStatus.closed:
                # if we match a closed rule return immediately
                return modifier
            matches.setdefault(modifier.status, modifier)
    return (
        matches.get(RuleStatus.open)
        or matches.get(RuleStatus.unknown)
        or RuleModifier(RuleStatus.closed, None)
    )
