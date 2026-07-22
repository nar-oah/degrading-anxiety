from collections.abc import Iterable
from datetime import datetime, timedelta
from types import SimpleNamespace
from unittest import TestCase
from alloc import Alloc
from degrading_anxiety_contracts.schedule import Arrange
from radicale import ALLOC_CALENDAR, NORMAL_CALENDAR


class FakeEvent:
    def __init__(self, start: datetime, duration: int) -> None:
        self.component = {"dtstart": SimpleNamespace(dt=start)}
        self.duration = timedelta(minutes=duration)
        self.saved = 0

    def get_duration(self) -> timedelta:
        return self.duration

    def set_end(self, end: datetime, move_dtstart: bool) -> None:
        self.component["dtstart"].dt = end - self.duration

    def save(self) -> None:
        self.saved += 1


class FakeRadicale:
    def __init__(self, events: dict[str, list[FakeEvent]]) -> None:
        self.events = events
        self.event_queries: list[tuple[str, datetime]] = []
        self.time_queries: list[tuple[str, datetime]] = []

    def get_times(
        self, name: str, day: datetime
    ) -> Iterable[tuple[datetime, datetime]]:
        self.time_queries.append((name, day))
        return map(
            lambda event: (
                event.component["dtstart"].dt,
                event.component["dtstart"].dt + event.duration,
            ),
            self.events[name],
        )

    def get_events(self, name: str, day: datetime) -> list[FakeEvent]:
        self.event_queries.append((name, day))
        return self.events[name]


class AllocTest(TestCase):
    def test_delay_only_reschedules_events_from_current_time(self) -> None:
        now = datetime(2026, 7, 22, 12)
        past = FakeEvent(now - timedelta(hours=2), 10)
        in_delay = FakeEvent(now + timedelta(minutes=5), 10)
        future = FakeEvent(now + timedelta(hours=1), 10)
        fixed = FakeEvent(now + timedelta(minutes=30), 15)
        radicale = FakeRadicale(
            {
                ALLOC_CALENDAR: [past, in_delay, future],
                NORMAL_CALENDAR: [fixed],
            }
        )

        Alloc(radicale, now, (NORMAL_CALENDAR,)).mod_schedule(15)

        self.assertEqual(radicale.time_queries, [(NORMAL_CALENDAR, now)])
        self.assertEqual(radicale.event_queries, [(ALLOC_CALENDAR, now)])
        self.assertEqual(past.saved, 0)
        self.assertEqual(in_delay.saved, 1)
        self.assertEqual(future.saved, 1)
        self.assertEqual(fixed.saved, 0)

    def test_alloc_avoids_normal_and_existing_alloc_events(self) -> None:
        now = datetime(2026, 7, 22, 12, 20)
        normal = FakeEvent(now.replace(minute=30), 30)
        allocated = FakeEvent(now.replace(hour=13, minute=10), 10)
        radicale = FakeRadicale(
            {ALLOC_CALENDAR: [allocated], NORMAL_CALENDAR: [normal]}
        )

        start, end = Alloc(radicale, now).get_schedule(10, Arrange.EARLY)

        self.assertEqual(
            (start, end),
            (now.replace(hour=13, minute=30), now.replace(hour=13, minute=40)),
        )
        self.assertEqual(
            radicale.time_queries,
            [(ALLOC_CALENDAR, now), (NORMAL_CALENDAR, now)],
        )
