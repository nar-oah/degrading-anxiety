from datetime import date, datetime, time, timedelta
import re
from celery import Celery
from alloc import Alloc
from new import add_schedule, add_user
from radicale import Radicale
from degrading_anxiety_contracts.schedule import REvent, TaskList

TOKEN_RE = re.compile(r"^[A-Za-z0-9_-]{43}$")
celery_app = Celery(
    "schedule_worker",
    broker="redis://redis:6379/0",
    backend="redis://redis:6379/1",
)


def get_radicale(token: str) -> Radicale:
    if isinstance(token, str) and bool(TOKEN_RE.fullmatch(token)):
        add_user(token)
        return Radicale(token)
    raise


@celery_app.task(name="schedule.add", pydantic=True, ignore_result=True)
def add_event(token: str, event: REvent) -> None:
    get_radicale(token).add_event(event)


@celery_app.task(name="schedule.delay", ignore_result=True)
def mod_schedule(token: str, minute: int) -> None:
    Alloc(get_radicale(token)).mod_schedule(minute)


@celery_app.task(name="schedule.alloc", pydantic=True, ignore_result=True)
def add_alloc(token: str, tasks: TaskList) -> None:
    add_schedule(get_radicale(token), tasks.root)


@celery_app.task(name="schedule.export")
def get_export(token: str, day: str) -> bytes:
    radicale = get_radicale(token)
    start = datetime.combine(date.fromisoformat(day), time.min)
    return radicale.get_calendar(start, start + timedelta(days=1))
