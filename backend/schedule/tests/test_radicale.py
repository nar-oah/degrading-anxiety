from datetime import datetime
from unittest import TestCase
from unittest.mock import Mock, call, patch
from caldav import Event as CalDAVEvent
from icalendar import Alarm, Calendar, Event, Todo
from radicale import COURSE_CALENDAR, NORMAL_CALENDAR, Radicale


def calendar_resource(*components: Event | Todo) -> CalDAVEvent:
    calendar = Calendar()
    for component in components:
        calendar.add_component(component)
    return CalDAVEvent(data=calendar.to_ical())


class EventSummariesTest(TestCase):
    def setUp(self) -> None:
        self.course_calendar = Mock()
        self.other_calendar = Mock()
        self.radicale = Radicale.__new__(Radicale)
        self.radicale.calendars = {
            COURSE_CALENDAR: self.course_calendar,
            NORMAL_CALENDAR: self.other_calendar,
        }

    def test_empty_calendar_has_no_summaries(self) -> None:
        self.course_calendar.search.return_value = []

        summaries = self.radicale.get_event_summaries(COURSE_CALENDAR)

        self.assertEqual(summaries, set())
        self.assertEqual(
            self.course_calendar.mock_calls, [call.search(event=True, expand=False)]
        )
        self.other_calendar.search.assert_not_called()

    def test_reads_all_vevent_summaries_without_date_filter(self) -> None:
        first = Event()
        first.add("SUMMARY", "数学;实验,进阶")
        first.add("DTSTART", datetime(2026, 9, 14, 8, 20))
        first.add("RRULE", {"FREQ": "WEEKLY", "COUNT": 16})
        alarm = Alarm()
        alarm.add("SUMMARY", "提醒名称")
        first.add_component(alarm)
        exception = Event()
        exception.add("SUMMARY", "数学调课")
        exception.add("RECURRENCE-ID", datetime(2026, 9, 21, 8, 20))
        later = Event()
        later.add("SUMMARY", "期末课程")
        later.add("DTSTART", datetime(2027, 1, 11, 8, 20))
        duplicate = Event()
        duplicate.add("SUMMARY", "数学;实验,进阶")
        todo = Todo()
        todo.add("SUMMARY", "待办名称")
        resources = [
            calendar_resource(first, exception, todo),
            calendar_resource(later),
            calendar_resource(duplicate, Event()),
        ]
        self.course_calendar.search.return_value = resources
        original_data = [resource.data for resource in resources]

        with patch.object(self.radicale, "get_events") as get_daily_events:
            summaries = self.radicale.get_event_summaries(COURSE_CALENDAR)

        self.assertEqual(summaries, {"数学;实验,进阶", "数学调课", "期末课程"})
        self.assertEqual(
            self.course_calendar.mock_calls, [call.search(event=True, expand=False)]
        )
        self.assertEqual([resource.data for resource in resources], original_data)
        get_daily_events.assert_not_called()
        self.other_calendar.search.assert_not_called()
