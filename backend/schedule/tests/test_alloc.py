from datetime import datetime, timedelta
from types import SimpleNamespace
from unittest import TestCase

from alloc import Alloc


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
    def __init__(self, events: list[FakeEvent]) -> None:
        self.events = events
        self.queries: list[datetime] = []

    def get_times(self, day: datetime):
        return map(
            lambda event: (
                event.component["dtstart"].dt,
                event.component["dtstart"].dt + event.duration,
            ),
            self.events,
        )

    def get_events(self, day: datetime) -> list[FakeEvent]:
        self.queries.append(day)
        return self.events


class AllocTest(TestCase):
    def test_delay_only_reschedules_events_from_current_time(self) -> None:
        now = datetime(2026, 7, 22, 12)
        past = FakeEvent(now - timedelta(hours=2), 10)
        in_delay = FakeEvent(now + timedelta(minutes=5), 10)
        future = FakeEvent(now + timedelta(hours=1), 10)
        radicale = FakeRadicale([past, in_delay, future])

        Alloc(radicale, now).mod_schedule(15)

        self.assertEqual(radicale.queries, [now])
        self.assertEqual(past.saved, 0)
        self.assertEqual(in_delay.saved, 1)
        self.assertEqual(future.saved, 1)
