from collections.abc import Iterable
from datetime import date, datetime, time, timedelta
from functools import reduce
from io import BytesIO
from itertools import chain, product
import pandas as pd
from degrading_anxiety_contracts.schedule import REvent

type Course = tuple[list[str], int, int]
TIME_TABLE = (
    (time(8, 20), time(10, 0)),
    (time(10, 10), time(11, 50)),
    (time(12, 0), time(12, 45)),
    (time(13, 30), time(15, 10)),
    (time(15, 20), time(17, 0)),
    (time(17, 10), time(17, 55)),
    (time(18, 0), time(19, 35)),
    (time(19, 45), time(21, 20)),
)
OFFSET = 1


def get_weeks(value: str) -> tuple[int, ...]:
    raw = value.split("(")[0]
    bounds = tuple(map(int, raw.replace("-", ",").split(",")))
    return bounds if "," in raw else tuple(range(bounds[0], bounds[-1] + 1))


class ClassParser:
    def __init__(self, excel: bytes, start: date) -> None:
        self.start = start
        self.df = pd.read_excel(BytesIO(excel), skiprows=1)

    def get_courses(self) -> Iterable[Course]:
        def get_cell(position: tuple[int, int]) -> Iterable[Course]:
            day, slot = position
            value = self.df.iloc[slot + OFFSET, day + OFFSET]
            rows = (
                value.strip().split("\n")
                if isinstance(value, str) and value.strip()
                else []
            )
            return map(lambda row: (row.strip().split("◇"), day, slot), rows)

        positions = product(range(7), range(len(TIME_TABLE)))
        return chain.from_iterable(map(get_cell, positions))

    def get_event(
        self,
        course: Course,
        weeks: tuple[int, ...],
        anchor_week: int,
    ) -> REvent:
        def get_time(location: str, slot: int) -> tuple[time, time]:
            changed = "M1-" not in location and slot == 1
            return (time(10, 25), time(12, 5)) if changed else TIME_TABLE[slot]

        def get_dt(value: time, week: int, day: int) -> datetime:
            target = self.start + timedelta(weeks=week - anchor_week, days=day)
            return datetime.combine(target, value)

        parts, day, slot = course
        start_time, end_time = get_time(parts[4], slot)
        repeat = (len(weeks), weeks[1] - weeks[0]) if len(weeks) > 1 else None
        return REvent(
            summary=parts[0],
            dtstart=get_dt(start_time, weeks[0], day),
            dtend=get_dt(end_time, weeks[0], day),
            location=parts[4],
            description=parts[1],
            repeat=repeat,
        )

    def get_events(self, course: Course, anchor_week: int) -> Iterable[REvent]:
        def add_week(
            runs: list[tuple[int, ...]],
            week: int,
        ) -> list[tuple[int, ...]]:
            current = runs[-1]
            same_gap = len(current) < 2 or week - current[-1] == current[-1] - current[-2]
            return [*runs[:-1], (*current, week)] if same_gap else [*runs, (week,)]

        weeks = get_weeks(course[0][3])
        runs = reduce(add_week, weeks[1:], [(weeks[0],)])
        return map(lambda value: self.get_event(course, value, anchor_week), runs)

    def get_parse(self) -> Iterable[REvent]:
        courses = list(self.get_courses())
        anchor_week = min(
            map(lambda value: get_weeks(value[0][3])[0], courses),
            default=1,
        )
        return chain.from_iterable(
            map(lambda value: self.get_events(value, anchor_week), courses)
        )
