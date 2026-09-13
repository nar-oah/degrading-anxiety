from datetime import date, datetime, time, timedelta
import re
from celery import Celery
from alloc import Alloc
from new import add_schedule, add_user
from radicale import COURSE_CALENDAR, EXAM_CALENDAR, NORMAL_CALENDAR, Radicale
from degrading_anxiety_contracts.schedule import REvent, REventList, TaskList

TOKEN_RE = re.compile(r"^[A-Za-z0-9_-]{43}$")
celery_app = Celery(
    "schedule_worker",
    broker="redis://redis:6379/0",
    backend="redis://redis:6379/1",
)


def get_radicale(token: str) -> Radicale:
    if isinstance(token, str) and bool(TOKEN_RE.fullmatch(token)):
        return add_user(token)
    raise


@celery_app.task(name="schedule.add", pydantic=True, ignore_result=True)
def add_event(token: str, event: REvent) -> None:
    get_radicale(token).add_event(NORMAL_CALENDAR, event)


@celery_app.task(
    name="schedule.course",
    pydantic=True,
    pydantic_strict=False,
    ignore_result=True,
)
def add_course(events: REventList, token: str) -> None:
    radicale = get_radicale(token)
    list(map(lambda event: radicale.add_event(COURSE_CALENDAR, event), events.root))


@celery_app.task(
    name="schedule.exam",
    pydantic=True,
    pydantic_strict=False,
    ignore_result=True,
)
def add_exam(events: REventList, token: str) -> None:
    radicale = get_radicale(token)
    list(map(lambda event: radicale.add_event(EXAM_CALENDAR, event), events.root))


@celery_app.task(name="schedule.delay", ignore_result=True)
def mod_schedule(token: str, minute: int) -> None:
    calendars = (NORMAL_CALENDAR, COURSE_CALENDAR, EXAM_CALENDAR)
    Alloc(get_radicale(token), calendars=calendars).mod_schedule(minute)


@celery_app.task(name="schedule.alloc", pydantic=True, ignore_result=True)
def add_alloc(token: str, tasks: TaskList) -> None:
    add_schedule(get_radicale(token), tasks.root)


@celery_app.task(name="schedule.export")
def get_export(token: str, day: str) -> bytes:
    radicale = get_radicale(token)
    start = datetime.combine(date.fromisoformat(day), time.min)
    return radicale.get_calendar(start, start + timedelta(days=1))
