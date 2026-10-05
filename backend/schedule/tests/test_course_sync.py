from datetime import datetime, timedelta
from unittest import TestCase
from unittest.mock import Mock, call, patch
import main
from degrading_anxiety_contracts.schedule import REvent, REventList
from radicale import COURSE_CALENDAR, Radicale


def course_event(summary: str, week: int = 0) -> REvent:
    start = datetime(2026, 9, 14, 8, 20) + timedelta(weeks=week)
    return REvent(
        summary=summary,
        dtstart=start,
        dtend=start + timedelta(hours=1),
        repeat=(2, 1),
    )


class CourseSyncTest(TestCase):
    def sync(self, events: list[REvent], existing_names: set[str]) -> Mock:
        radicale = Mock(spec=Radicale)
        radicale.get_event_summaries.return_value = existing_names
        radicale.add_event.side_effect = lambda name, event: existing_names.add(
            event.summary
        )
        with patch.object(main, "get_radicale", return_value=radicale) as get_radicale:
            main.sync_course.run(REventList(root=events).model_dump(mode="json"), "token")
        get_radicale.assert_called_once_with("token")
        return radicale

    def test_empty_calendar_adds_all_courses(self) -> None:
        events = [course_event("数学"), course_event("物理")]

        radicale = self.sync(events, set())

        self.assertEqual(
            radicale.mock_calls,
            [call.get_event_summaries(COURSE_CALENDAR)]
            + [call.add_event(COURSE_CALENDAR, event) for event in events],
        )

    def test_existing_course_names_are_not_added(self) -> None:
        events = [course_event("数学"), course_event("数学", week=4)]

        radicale = self.sync(events, {"数学"})

        self.assertEqual(radicale.mock_calls, [call.get_event_summaries(COURSE_CALENDAR)])

    def test_only_new_courses_are_added(self) -> None:
        existing = course_event("数学")
        new = course_event("物理")

        radicale = self.sync([existing, new], {"数学"})

        self.assertEqual(
            radicale.mock_calls,
            [call.get_event_summaries(COURSE_CALENDAR), call.add_event(COURSE_CALENDAR, new)],
        )

    def test_new_courses_keep_reminders_from_current_import(self) -> None:
        existing = course_event("数学")
        new = course_event("物理").model_copy(update={"alarms": [30]})

        radicale = self.sync([existing, new], {"数学"})

        radicale.add_event.assert_called_once_with(COURSE_CALENDAR, new)
        self.assertEqual(radicale.add_event.call_args.args[1].alarms, [30])

    def test_all_segments_of_new_course_are_added(self) -> None:
        first = course_event("新增课程")
        second = course_event("新增课程", week=4)
        events = [first, course_event("已有课程"), second]

        radicale = self.sync(events, {"已有课程"})

        self.assertEqual(
            radicale.mock_calls,
            [
                call.get_event_summaries(COURSE_CALENDAR),
                call.add_event(COURSE_CALENDAR, first),
                call.add_event(COURSE_CALENDAR, second),
            ],
        )

    def test_empty_course_list_does_not_change_existing_calendar(self) -> None:
        existing_names = {"数学"}

        radicale = self.sync([], existing_names)

        self.assertEqual(existing_names, {"数学"})
        self.assertEqual(radicale.mock_calls, [call.get_event_summaries(COURSE_CALENDAR)])

    def test_repeated_sync_does_not_add_courses_again(self) -> None:
        events = [course_event("数学"), course_event("物理")]
        existing_names: set[str] = set()
        self.sync(events, existing_names)

        radicale = self.sync(events, existing_names)

        self.assertEqual(radicale.mock_calls, [call.get_event_summaries(COURSE_CALENDAR)])
