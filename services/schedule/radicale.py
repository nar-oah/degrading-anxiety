from collections.abc import Iterable
from dataclasses import dataclass, field
from caldav.davclient import DAVClient
from caldav import Event
from datetime import datetime, timedelta, tzinfo
from icalendar import Alarm, Component, Calendar

type Events = Iterable[tuple[datetime, datetime]]
type Rrule = dict[str, str | int]
WEEK_DAYS = ["MO", "TU", "WE", "TH", "FR", "SA", "SU"]
CALENDAR = "Voice Calendar"
URL = "http://127.0.0.1:5232/"


@dataclass
class REvent:
    summary: str
    dtstart: datetime
    dtend: datetime
    location: str = ""
    description: str = ""
    alarms: list[int] = field(default_factory=lambda: [15])
    repeat: tuple[int, int] | None = None


class Radicale:
    def __init__(self, token: str) -> None:
        with DAVClient(url=URL, username=token, password=token) as client:
            self.principal = client.principal()

    def add_event(self, name: str, event: REvent, rrule: Rrule | None = None) -> None:
        def get_rrule(c: int, i: int, day: str) -> Rrule:
            return {"freq": "WEEKLY", "count": c, "byday": day, "interval": i}

        calendar = self.principal.calendar(name)
        day = WEEK_DAYS[event.dtstart.weekday()]
        repeat = event.repeat
        get_weekly = get_rrule(*repeat, day) if isinstance(repeat, tuple) else None
        create = calendar.add_event(
            summary=event.summary,
            dtstart=event.dtstart,
            dtend=event.dtend,
            location=event.location,
            description=event.description,
            rrule=rrule if isinstance(rrule, dict) else get_weekly,
        )
        for minutes in event.alarms:
            alarm = Alarm()
            alarm.add("action", "DISPLAY")
            alarm.add("trigger", timedelta(minutes=-minutes))
            alarm.add("description", f"{minutes}分钟前提醒")
            component: Component = create.component
            component.add_component(alarm)
        create.save()

    def get_events(self, name: str, day: datetime) -> list[Event]:
        calendar = self.principal.calendar(name)
        return calendar.search(start=day, end=day.replace(hour=23), expand=True)

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

    def _get_calendar(self, name: str):
        def is_calendar(calendar) -> bool:
            return calendar.get_display_name() == name

        calendars = list(filter(is_calendar, self.principal.get_calendars()))
        return (
            calendars[0]
            if len(calendars) > 0
            else self.principal.make_calendar(name=name)
        )

    def _add_clalendar_head(self, calendar: Calendar) -> None:
        calendar.add("prodid", "-//voice-calendar//naroah.top//")
        calendar.add("version", "2.0")

    def add_calendar(self, name: str) -> None:
        self._get_calendar(name)

    def get_calendar(self, start: datetime, end: datetime) -> bytes:
        def add_vevent(calendar: Calendar, event: Event) -> None:
            source_calendar = Calendar.from_ical(event.data)
            vevents = filter(lambda c: c.name == "VEVENT", source_calendar.walk())
            list(map(lambda vevent: calendar.add_component(vevent), vevents))

        calendar = self._get_calendar(CALENDAR)
        events = calendar.search(event=True, start=start, end=end, expand=False)
        output = Calendar()
        self._add_clalendar_head(output)
        list(map(lambda event: add_vevent(output, event), events))  # type: ignore
        return output.to_ical()


if __name__ == "__main__":
    from collections.abc import Callable

    radicale = Radicale("test")
    get_dt: Callable[[int], datetime] = lambda hour=0: (
        datetime.now() + timedelta(hours=1 + hour)
    )
    revent = REvent(summary="测试", dtstart=get_dt(), dtend=get_dt(1), alarms=[15, -15])
    radicale.add_event("test", event=revent)
