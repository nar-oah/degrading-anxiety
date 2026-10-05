from datetime import datetime, timedelta
from unittest import TestCase
from unittest.mock import Mock, call, patch
from caldav import Event as CalDAVEvent
from icalendar import Alarm, Calendar, Event, Todo
import main
from degrading_anxiety_contracts.schedule import REvent, REventList
from radicale import COURSE_CALENDAR, NORMAL_CALENDAR, Radicale


def calendar_resource(*components: Event | Todo) -> CalDAVEvent:
    calendar = Calendar()
    for component in components:
        calendar.add_component(component)
    return CalDAVEvent(data=calendar.to_ical())


def reminder_alarm(minutes: int) -> Alarm:
    alarm = Alarm()
    alarm.add("ACTION", "DISPLAY")
    alarm.add("TRIGGER", timedelta(minutes=-minutes))
    alarm.add("DESCRIPTION", f"{minutes}分钟前提醒")
    return alarm


class RemindersTest(TestCase):
    def setUp(self) -> None:
        self.course_calendar = Mock()
        self.radicale = Radicale.__new__(Radicale)
        self.radicale.calendars = {COURSE_CALENDAR: self.course_calendar}

    def test_new_event_defaults_to_fifteen_minute_reminder(self) -> None:
        start = datetime(2026, 9, 14, 8, 20)
        event = REvent(summary="课程", dtstart=start, dtend=start + timedelta(hours=1))
        resource = calendar_resource(Event())
        self.course_calendar.add_event.return_value = resource

        with patch.object(resource, "save") as save_event:
            self.radicale.add_event(COURSE_CALENDAR, event)

        self.assertEqual(event.alarms, [15])
        (alarm,) = resource.component.walk("VALARM")
        self.assertEqual(alarm["TRIGGER"].dt, timedelta(minutes=-15))
        self.assertEqual(str(alarm["DESCRIPTION"]), "15分钟前提醒")
        save_event.assert_called_once_with()

    def test_updates_matching_reminders_and_preserves_recurring_event(self) -> None:
        component = Event()
        component.add("UID", "recurring-course")
        component.add("SUMMARY", "数学")
        component.add("DTSTART", datetime(2026, 9, 14, 8, 20))
        component.add("DTEND", datetime(2026, 9, 14, 9, 20))
        component.add("RRULE", {"FREQ": "WEEKLY", "COUNT": 16, "BYDAY": "MO"})
        component.add("EXDATE", datetime(2026, 9, 21, 8, 20))
        component.add("LOCATION", "原教室")
        component.add("DESCRIPTION", "课程备注")
        component.add("SEQUENCE", 3)
        alarm = reminder_alarm(15)
        alarm["TRIGGER"].params["RELATED"] = "START"
        alarm["DESCRIPTION"].params["LANGUAGE"] = "zh"
        component.add_component(alarm)
        component.add_component(reminder_alarm(0))
        component.add_component(reminder_alarm(5))
        component.add_component(reminder_alarm(-15))
        missing_trigger = Alarm()
        missing_trigger.add("ACTION", "DISPLAY")
        component.add_component(missing_trigger)
        resource = calendar_resource(component)
        self.course_calendar.search.return_value = [resource]
        original = Calendar.from_ical(resource.data).walk("VEVENT")[0]
        original_properties = dict(original)
        special_alarms = [alarm.to_ical() for alarm in original.walk("VALARM")[1:]]

        with (
            patch.object(resource, "save", wraps=resource.save) as save_event,
            patch.object(resource, "_create") as persist_event,
            patch.object(resource, "delete") as delete_event,
        ):
            self.radicale.update_reminders(COURSE_CALENDAR, 15, 30)

        updated = Calendar.from_ical(resource.data).walk("VEVENT")[0]
        updated_alarms = updated.walk("VALARM")
        self.assertEqual(dict(updated), original_properties)
        self.assertEqual(updated_alarms[0]["TRIGGER"].dt, timedelta(minutes=-30))
        self.assertEqual(str(updated_alarms[0]["DESCRIPTION"]), "30分钟前提醒")
        self.assertEqual(updated_alarms[0]["TRIGGER"].params["RELATED"], "START")
        self.assertEqual(updated_alarms[0]["DESCRIPTION"].params["LANGUAGE"], "zh")
        self.assertEqual(
            [alarm.to_ical() for alarm in updated_alarms[1:]], special_alarms
        )
        self.course_calendar.search.assert_called_once_with(event=True, expand=False)
        self.course_calendar.add_event.assert_not_called()
        self.course_calendar.delete.assert_not_called()
        save_event.assert_called_once_with(
            increase_seqno=False, only_this_recurrence=False
        )
        persist_event.assert_called_once()
        delete_event.assert_not_called()

    def test_updates_all_vevents_in_resource_without_changing_todo_alarms(self) -> None:
        first = Event()
        first.add("UID", "course")
        first.add("RRULE", {"FREQ": "WEEKLY", "COUNT": 16})
        first.add_component(reminder_alarm(15))
        exception = Event()
        exception.add("UID", "course")
        exception.add("RECURRENCE-ID", datetime(2026, 9, 21, 8, 20))
        exception.add_component(reminder_alarm(15))
        todo = Todo()
        todo.add_component(reminder_alarm(15))
        resource = calendar_resource(first, exception, todo)
        self.course_calendar.search.return_value = [resource]

        with patch.object(resource, "save") as save_event:
            self.radicale.update_reminders(COURSE_CALENDAR, 15, 30)

        calendar = Calendar.from_ical(resource.data)
        self.assertEqual(
            [
                alarm["TRIGGER"].dt
                for event in calendar.walk("VEVENT")
                for alarm in event.walk("VALARM")
            ],
            [timedelta(minutes=-30), timedelta(minutes=-30)],
        )
        self.assertEqual(
            calendar.walk("VTODO")[0].walk("VALARM")[0]["TRIGGER"].dt,
            timedelta(minutes=-15),
        )
        save_event.assert_called_once_with(
            increase_seqno=False, only_this_recurrence=False
        )

    def test_resource_with_only_special_reminders_is_not_saved(self) -> None:
        component = Event()
        component.add_component(reminder_alarm(0))
        component.add_component(reminder_alarm(5))
        resource = calendar_resource(component)
        self.course_calendar.search.return_value = [resource]
        original_data = resource.data

        with patch.object(resource, "save") as save_event:
            self.radicale.update_reminders(COURSE_CALENDAR, 15, 30)

        self.assertEqual(resource.data, original_data)
        save_event.assert_not_called()

    def test_zero_minute_reminders_are_preserved_when_old_default_is_zero(self) -> None:
        self.radicale.update_reminders(COURSE_CALENDAR, 0, 30)

        self.course_calendar.search.assert_not_called()


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

    def test_sync_never_deletes_or_modifies_existing_events(self) -> None:
        component = Event()
        component.add("SUMMARY", "已有课程")
        component.add("LOCATION", "原教室")
        resource = calendar_resource(component)
        original_data = resource.data
        self.course_calendar.search.return_value = [resource]
        start = datetime(2026, 9, 14, 8, 20)
        existing = REvent(
            summary="已有课程", dtstart=start, dtend=start + timedelta(hours=1),
            location="新教室",
        )
        new = existing.model_copy(update={"summary": "新增课程"})
        events = REventList(root=[existing, new]).model_dump(mode="json")

        with (
            patch.object(main, "get_radicale", return_value=self.radicale),
            patch.object(self.radicale, "add_event") as add_event,
            patch.object(resource, "save") as save_event,
            patch.object(resource, "delete") as delete_event,
        ):
            main.sync_course.run(events, "token")

        add_event.assert_called_once_with(COURSE_CALENDAR, new)
        save_event.assert_not_called()
        delete_event.assert_not_called()
        self.assertEqual(resource.data, original_data)
        self.assertEqual(
            self.course_calendar.mock_calls, [call.search(event=True, expand=False)]
        )
        self.other_calendar.search.assert_not_called()
