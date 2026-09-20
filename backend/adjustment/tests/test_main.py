from datetime import date, datetime, time
from unittest import TestCase
from degrading_anxiety_contracts.schedule import REvent, REventList
from main import mod_courses


class AdjustmentTest(TestCase):
    def test_holiday_removes_recurrences_and_makeup_uses_original(self) -> None:
        course = REvent(
            summary="数学",
            dtstart=datetime(2026, 9, 21, 8, 20),
            dtend=datetime(2026, 9, 21, 10),
            location="A101",
            description="张老师",
            alarms=[30, 5],
            repeat=(4, 1),
        )
        source = REvent(
            summary="英语",
            dtstart=datetime(2026, 10, 5, 10, 10),
            dtend=datetime(2026, 10, 5, 11, 50),
            location="B202",
            description="李老师",
            alarms=[10],
        )
        result = mod_courses(
            REventList(root=[course, source]),
            [(date(2026, 9, 25), date(2026, 10, 7))],
            [(date(2026, 9, 20), date(2026, 10, 5))],
        ).root

        self.assertEqual(
            [(event.summary, event.dtstart.date()) for event in result],
            [
                ("数学", date(2026, 9, 21)),
                ("数学", date(2026, 10, 12)),
                ("数学", date(2026, 9, 20)),
                ("英语", date(2026, 9, 20)),
            ],
        )
        copied = result[3]
        self.assertEqual(copied.dtstart.time(), time(10, 10))
        self.assertEqual(copied.dtend.time(), time(11, 50))
        self.assertEqual(copied.location, "B202")
        self.assertEqual(copied.description, "李老师")
        self.assertEqual(copied.alarms, [10])
        self.assertIsNone(copied.repeat)
        self.assertEqual(source.dtstart.date(), date(2026, 10, 5))

    def test_makeup_copies_matching_occurrence_from_recurrence(self) -> None:
        course = REvent(
            summary="物理",
            dtstart=datetime(2026, 9, 21, 8, 20),
            dtend=datetime(2026, 9, 21, 10),
            repeat=(3, 1),
        )
        result = mod_courses(
            REventList(root=[course]),
            [(date(2026, 9, 25), date(2026, 10, 7))],
            [(date(2026, 9, 20), date(2026, 10, 5))],
        ).root

        self.assertEqual(
            [event.dtstart.date() for event in result],
            [date(2026, 9, 21), date(2026, 9, 20)],
        )
