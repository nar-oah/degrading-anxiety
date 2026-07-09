from datetime import date, datetime, time, timedelta
import re
from celery import Celery
from new import add_user
from radicale import Radicale

TOKEN_RE = re.compile(r"^[A-Za-z0-9_-]{43}$")
celery_app = Celery(
    "schedule_worker",
    broker="redis://redis:6379/0",
    backend="redis://redis:6379/1",
)


def get_radicale(token: str) -> Radicale:
    def is_token() -> bool:
        return isinstance(token, str) and bool(TOKEN_RE.fullmatch(token))

    def fail() -> None:
        raise

    add_user(token) if is_token() else fail()
    return Radicale(token)


@celery_app.task(name="schedule.export")
def get_export(token: str, date: date) -> bytes:
    radicale = get_radicale(token)
    start = datetime.combine(date, time.min)
    return radicale.get_calendar(start, start + timedelta(days=1))
