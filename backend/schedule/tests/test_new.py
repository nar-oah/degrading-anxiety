from datetime import datetime
from unittest import TestCase
from unittest.mock import Mock, patch
from degrading_anxiety_contracts.schedule import Arrange, REvent, Task
from new import add_schedule
from radicale import ALLOC_CALENDAR


class NewScheduleTest(TestCase):
    def test_event_without_explicit_alarms_defaults_to_fifteen_minutes(self) -> None:
        event = REvent(
            summary="默认提醒",
            dtstart=datetime(2026, 9, 21, 8),
            dtend=datetime(2026, 9, 21, 9),
        )
        self.assertEqual(event.alarms, [15])

    def test_alloc_uses_default_or_requested_reminder_and_preserves_normal_alarm(self) -> None:
        tasks = [
            Task(description=arrange.value, duration=10, arrange=arrange)
            for arrange in (Arrange.NORMAL, Arrange.EARLY, Arrange.LATE)
        ]
        for requested in (None, 30, 0):
            with (
                self.subTest(reminder_minutes=requested),
                patch("new.Alloc") as alloc,
            ):
                radicale = Mock()
                alloc.return_value.get_schedule.return_value = (
                    datetime(2026, 9, 21, 8),
                    datetime(2026, 9, 21, 8, 10),
                )
                kwargs = {} if requested is None else {"reminder_minutes": requested}
                add_schedule(radicale, tasks, **kwargs)

                events = [call.args[1] for call in radicale.add_event.call_args_list]
                expected_minutes = 15 if requested is None else requested
                self.assertEqual(
                    [event.alarms for event in events],
                    [[0], [expected_minutes], [expected_minutes]],
                )
                self.assertEqual(
                    [call.args[0] for call in radicale.add_event.call_args_list],
                    [ALLOC_CALENDAR] * 3,
                )
                self.assertEqual(
                    [event.summary for event in events],
                    [task.description for task in tasks],
                )
