from collections.abc import Iterable
from itertools import chain
from caldav.davclient import DAVClient
from caldav import Calendar as CalDAVCalendar, Event
from datetime import datetime, timedelta, tzinfo
from icalendar import Alarm, Component, Calendar
from degrading_anxiety_contracts.schedule import REvent

type Events = Iterable[tuple[datetime, datetime]]
type Rrule = dict[str, str | int]
WEEK_DAYS = ["MO", "TU", "WE", "TH", "FR", "SA", "SU"]
ALLOC_CALENDAR = "Alloc"
NORMAL_CALENDAR = "Normal"
CALENDARS = (ALLOC_CALENDAR, NORMAL_CALENDAR)
URL = "http://radicale:5232/"


class Radicale:
    def __init__(self, token: str) -> None:
        with DAVClient(url=URL, username=token, password=token) as client:
            self.principal = client.principal()
            self.calendars = dict(
                map(lambda name: (name, self.add_calendar(name)), CALENDARS)
            )

    def add_calendar(self, name: str) -> CalDAVCalendar:
        calendars = self.principal.get_calendars()
        calendar = next(
            filter(lambda value: value.get_display_name() == name, calendars),
            None,
        )
        return (
            calendar
            if isinstance(calendar, CalDAVCalendar)
            else self.principal.make_calendar(name=name)
        )

    def add_event(
        self, name: str, event: REvent, rrule: Rrule | None = None
    ) -> None:
        def get_rrule(c: int, i: int, day: str) -> Rrule:
            return {"freq": "WEEKLY", "count": c, "byday": day, "interval": i}

        day = WEEK_DAYS[event.dtstart.weekday()]
        repeat = event.repeat
        get_weekly = get_rrule(*repeat, day) if isinstance(repeat, tuple) else None
        create: Event = self.calendars[name].add_event(
            summary=event.summary,
            dtstart=event.dtstart,
            dtend=event.dtend,
            location=event.location,
            description=event.description,
            rrule=rrule if isinstance(rrule, dict) else get_weekly,
        )

        def add_alarm(minutes: int) -> None:
            alarm = Alarm()
            alarm.add("action", "DISPLAY")
            alarm.add("trigger", timedelta(minutes=-minutes))
            alarm.add("description", f"{minutes}分钟前提醒")
            component: Component = create.component
            component.add_component(alarm)

        list(map(add_alarm, event.alarms))
        create.save()

    def get_events(self, name: str, day: datetime) -> list[Event]:
        events = self.calendars[name].search(
            start=day, end=day.replace(hour=23), expand=True
        )
        assert isinstance(events, list)
        return events

    def get_times(self, name: str, day: datetime) -> Events:
        def get_local(dt: datetime) -> datetime:
            return (
                dt.astimezone().replace(tzinfo=None)
                if isinstance(dt.tzinfo, tzinfo)
                else dt
            )

        def get_time(event: Event) -> tuple[datetime, datetime]:
            return (
                get_local(event.component.get("dtstart").dt),
                get_local(event.component.get("dtend").dt),
            )

        return map(lambda x: get_time(x), self.get_events(name, day))

    def get_calendar(self, start: datetime, end: datetime) -> bytes:
        def add_head(calendar: Calendar) -> None:
            calendar.add("prodid", "-//degrading-anxiety//naroah.top//")
            calendar.add("version", "2.0")

        def add_vevent(calendar: Calendar, event: Event) -> None:
            source_calendar = Calendar.from_ical(event.data)
            vevents = filter(lambda c: c.name == "VEVENT", source_calendar.walk())
            list(map(lambda vevent: calendar.add_component(vevent), vevents))

        def get_events(calendar: CalDAVCalendar) -> list[Event]:
            events = calendar.search(event=True, start=start, end=end, expand=False)
            assert isinstance(events, list)
            return events

        events = chain.from_iterable(map(get_events, self.calendars.values()))
        output = Calendar()
        add_head(output)
        list(map(lambda event: add_vevent(output, event), events))
        return output.to_ical()


if __name__ == "__main__":
    from collections.abc import Callable

    radicale = Radicale("test")
    get_dt: Callable[[int], datetime] = lambda hour=0: (
        datetime.now() + timedelta(hours=1 + hour)
    )
    revent = REvent(summary="测试", dtstart=get_dt(), dtend=get_dt(1), alarms=[15, -15])
    radicale.add_event(NORMAL_CALENDAR, event=revent)
