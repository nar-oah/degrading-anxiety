from collections.abc import Iterable
from datetime import datetime, timedelta
from unittest import TestCase
from unittest.mock import patch
import main
from degrading_anxiety_contracts.schedule import REvent, REventList, Task
from new import add_schedule
from radicale import ALLOC_CALENDAR, COURSE_CALENDAR, EXAM_CALENDAR, NORMAL_CALENDAR


class FakeRadicale:
    def __init__(self) -> None:
        self.added: list[tuple[str, REvent]] = []

    def add_event(self, name: str, event: REvent) -> None:
        self.added.append((name, event))

    def get_times(
        self, name: str, day: datetime
    ) -> Iterable[tuple[datetime, datetime]]:
        return iter(())


class CalendarRoutesTest(TestCase):
    def test_add_event_uses_normal_calendar(self) -> None:
        radicale = FakeRadicale()
        start = datetime(2026, 7, 22, 12)
        event = REvent(summary="normal", dtstart=start, dtend=start + timedelta(hours=1))

        with patch.object(main, "get_radicale", return_value=radicale):
            main.add_event.run("token", event)

        self.assertEqual(radicale.added, [(NORMAL_CALENDAR, event)])

    def test_add_course_uses_course_calendar(self) -> None:
        radicale = FakeRadicale()
        start = datetime(2026, 9, 14, 8, 20)
        event = REvent(summary="course", dtstart=start, dtend=start + timedelta(hours=1))
        events = REventList(root=[event]).model_dump(mode="json")

        with patch.object(main, "get_radicale", return_value=radicale):
            main.add_course.run(events, "token")

        self.assertEqual(radicale.added, [(COURSE_CALENDAR, event)])

    def test_add_exam_uses_exam_calendar(self) -> None:
        radicale = FakeRadicale()
        start = datetime(2026, 9, 17, 10, 10)
        event = REvent(summary="exam", dtstart=start, dtend=start + timedelta(hours=1))
        events = REventList(root=[event]).model_dump(mode="json")

        with patch.object(main, "get_radicale", return_value=radicale):
            main.add_exam.run(events, "token")

        self.assertEqual(radicale.added, [(EXAM_CALENDAR, event)])

    def test_add_alloc_uses_alloc_calendar(self) -> None:
        radicale = FakeRadicale()

        add_schedule(radicale, [Task(description="alloc", duration=10)])

        self.assertEqual(
            list(map(lambda value: value[0], radicale.added)), [ALLOC_CALENDAR]
        )
