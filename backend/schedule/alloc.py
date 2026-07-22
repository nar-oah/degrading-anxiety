from collections.abc import Callable, Iterable
from datetime import date, datetime, time, timedelta
from itertools import chain
from caldav import Event
from intervaltree import Interval, IntervalTree
from degrading_anxiety_contracts.schedule import Arrange
from radicale import ALLOC_CALENDAR, CALENDARS, Radicale


class Alloc:
    def __init__(
        self,
        radicale: Radicale,
        day: datetime | None = None,
        calendars: Iterable[str] = CALENDARS,
    ) -> None:
        def get_pieces(name: str) -> Iterable[tuple[int, int]]:
            get_piece = lambda x: (x.hour * 60) + x.minute
            events = radicale.get_times(name, self.day)
            return map(lambda x: (get_piece(x[0]) - 15, get_piece(x[1]) + 10), events)

        self.day = day if isinstance(day, datetime) else datetime.now()
        start = (self.day.hour * 60) + self.day.minute
        self.slots = IntervalTree([Interval(start, 21 * 60)])
        self.radicale = radicale
        pieces = chain.from_iterable(map(get_pieces, calendars))
        list(map(lambda piece: self.slots.chop(*piece), pieces))

    def get_schedule(self, dur: int, range=Arrange.NORMAL) -> tuple[datetime, datetime]:
        def get_key() -> Callable[[Interval], int]:
            match range:
                case Arrange.EARLY:
                    return lambda x: x.begin
                case Arrange.LATE:
                    return lambda x: -x.begin
                case Arrange.NORMAL:
                    return lambda x: x.end - x.begin

        def get_alloc(key: Callable[[Interval], int]) -> tuple[int, int]:
            is_alloc: Callable[[Interval], bool] = lambda x: (x.end - x.begin) >= dur
            start: int = sorted(filter(is_alloc, self.slots), key=key)[0].begin
            return start, start + dur

        def get_time(time: int) -> datetime:
            return self.day.replace(hour=time // 60, minute=time % 60)

        start, end = get_alloc(get_key())
        self.slots.chop(start, end + 1)
        return get_time(start), get_time(end)

    def mod_schedule(self, delay: int = 0) -> None:
        def get_dur(event: Event) -> int:
            delta = event.get_duration()
            return int(delta.total_seconds() // 60)

        def get_start(event: Event) -> float:
            start: datetime = event.component.get("dtstart").dt
            return start.timestamp()

        def mod_event(event: Event, schedule: tuple[datetime, datetime]) -> None:
            _, end = schedule
            event.set_end(end, True)
            event.save()

        def get_piece(time: datetime) -> int:
            return (time.hour * 60) + time.minute

        current = self.day
        delay_dt = current + timedelta(minutes=delay)
        events = self.radicale.get_events(ALLOC_CALENDAR, current)
        events = filter(lambda event: get_start(event) >= current.timestamp(), events)
        self.slots.chop(get_piece(current), get_piece(delay_dt))
        self.day = delay_dt
        for event in events:
            mod_event(event, self.get_schedule(get_dur(event)))


if __name__ == "__main__":
    name = "test_ielts"
    dt = datetime.combine(date.today(), time(hour=8)) + timedelta(days=2)
    Alloc(Radicale("test"), dt).mod_schedule(5)
