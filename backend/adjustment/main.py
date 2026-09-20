from datetime import date, timedelta
from itertools import chain
from celery import Celery
from degrading_anxiety_contracts.schedule import REvent, REventList
from parser.adjustment import get_adjustment

celery_app = Celery(
    "adjustment_worker",
    broker="redis://redis:6379/0",
    backend="redis://redis:6379/1",
)


def get_events(events: REventList) -> list[REvent]:
    def get_occurrences(event: REvent) -> list[REvent]:
        count, interval = event.repeat if isinstance(event.repeat, tuple) else (1, 1)
        return list(
            map(
                lambda index: event.model_copy(
                    update={
                        "dtstart": event.dtstart + timedelta(weeks=index * interval),
                        "dtend": event.dtend + timedelta(weeks=index * interval),
                        "repeat": None,
                    }
                ),
                range(count),
            )
        )

    return list(chain.from_iterable(map(get_occurrences, events.root)))


def mod_courses(
    events: REventList,
    holidays: list[tuple[date, date]],
    makeups: list[tuple[date, date]],
) -> REventList:
    original = get_events(events)
    remaining = list(
        filter(
            lambda event: not any(
                map(
                    lambda span: span[0] <= event.dtstart.date() <= span[1],
                    holidays,
                )
            ),
            original,
        )
    )

    def get_makeup(rule: tuple[date, date]) -> list[REvent]:
        target, source = rule
        offset = timedelta(days=(target - source).days)
        return list(
            map(
                lambda event: event.model_copy(
                    update={
                        "dtstart": event.dtstart + offset,
                        "dtend": event.dtend + offset,
                    }
                ),
                filter(lambda event: event.dtstart.date() == source, original),
            )
        )

    return REventList(root=[*remaining, *chain.from_iterable(map(get_makeup, makeups))])


@celery_app.task(name="adjustment.apply", pydantic=True, pydantic_strict=False)
def apply(events: REventList, pdf: bytes) -> REventList:
    holidays, makeups = get_adjustment(pdf)
    return mod_courses(events, holidays, makeups)
