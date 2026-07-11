from collections.abc import Callable, Iterable
from datetime import date, datetime, time, timedelta
from caldav import Event
from intervaltree import Interval, IntervalTree
from radicale import Radicale


class Alloc:
    def __init__(self, radicale: Radicale, day: datetime | None = None) -> None:
        def get_pieces() -> Iterable[tuple[int, int]]:
            get_piece = lambda x: (x.hour * 60) + x.minute
            events = radicale.get_times(self.day)
            return map(lambda x: (get_piece(x[0]) - 15, get_piece(x[1]) + 10), events)

        self.day = day if isinstance(day, datetime) else datetime.now()
        start = (self.day.hour * 60) + self.day.minute
        self.slots = IntervalTree([Interval(start, 21 * 60)])
        self.radicale = radicale
        for start, end in get_pieces():
            self.slots.chop(start, end)

    def get_schedule(
        self, dur: int, key: Callable[[Interval], int] = lambda x: x.end - x.begin
    ) -> tuple[datetime, datetime]:
        def get_alloc() -> tuple[int, int]:
            is_alloc: Callable[[Interval], bool] = lambda x: (x.end - x.begin) >= dur
            start: int = sorted(filter(is_alloc, self.slots), key=key)[0].begin
            return start, start + dur

        def get_time(time: int) -> datetime:
            return self.day.replace(hour=time // 60, minute=time % 60)

        start, end = get_alloc()
        self.slots.chop(start, end + 1)
        return get_time(start), get_time(end)

    def mod_schedule(self, delay: int = 0) -> None:
        def get_dur(event: Event) -> int:
            delta = event.get_duration()
            return int(delta.total_seconds() // 60)

        def mod_event(event: Event, schedule: tuple[datetime, datetime]) -> None:
            _, end = schedule
            event.set_end(end, True)
            event.save()

        def get_piece(time: datetime) -> int:
            return (time.hour * 60) + time.minute

        delay_dt = self.day + timedelta(minutes=delay)
        events = self.radicale.get_events(delay_dt)
        self.slots.chop(get_piece(self.day), get_piece(delay_dt))
        self.day = delay_dt
        for event in events:
            mod_event(event, self.get_schedule(get_dur(event)))


if __name__ == "__main__":
    name = "test_ielts"
    dt = datetime.combine(date.today(), time(hour=8)) + timedelta(days=2)
    Alloc(Radicale("test"), dt).mod_schedule(5)
