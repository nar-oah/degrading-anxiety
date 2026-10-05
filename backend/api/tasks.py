from datetime import date
from celery import Celery, chain
from celery.result import AsyncResult
from pydantic import BaseModel

celery_app = Celery(
    "api",
    broker="redis://redis:6379/0",
    backend="redis://redis:6379/1",
)


def add_task(
    name: str, token: str, value: BaseModel | int | str, *minutes: int
) -> AsyncResult:
    arg = value.model_dump(mode="json") if isinstance(value, BaseModel) else value
    return celery_app.send_task(
        name,
        args=[token, arg, *minutes],
        queue="schedule",
    )


def add_course_task(token: str, day: date, reminder_minutes: int = 15) -> AsyncResult:
    return _add_course_task(token, day, "schedule.course", reminder_minutes)


def add_course_sync_task(token: str, day: date, reminder_minutes: int = 15) -> AsyncResult:
    return _add_course_task(token, day, "schedule.course.sync", reminder_minutes)


def _add_course_task(
    token: str, day: date, schedule_task: str, reminder_minutes: int
) -> AsyncResult:
    get_course = celery_app.signature(
        "course.get",
        args=[{"date": day.isoformat()}],
        kwargs={"reminder_minutes": reminder_minutes},
        queue="course",
    )
    add_course = celery_app.signature(
        schedule_task,
        args=[token],
        queue="schedule",
    )
    return chain(get_course, add_course).apply_async()


def add_exam_task(token: str, excel: bytes, reminder_minutes: int = 15) -> AsyncResult:
    get_exam = celery_app.signature(
        "exam.get",
        args=[excel],
        kwargs={"reminder_minutes": reminder_minutes},
        queue="exam",
    )
    add_exam = celery_app.signature(
        "schedule.exam",
        args=[token],
        queue="schedule",
    )
    return chain(get_exam, add_exam).apply_async()


def add_adjustment_task(
    token: str, day: date, pdf: bytes, reminder_minutes: int = 15
) -> AsyncResult:
    get_course = celery_app.signature(
        "course.get",
        args=[{"date": day.isoformat()}],
        kwargs={"reminder_minutes": reminder_minutes},
        queue="course",
    )
    apply_adjustment = celery_app.signature(
        "adjustment.apply",
        args=[pdf],
        kwargs={"reminder_minutes": reminder_minutes},
        queue="adjustment",
    )
    replace_course = celery_app.signature(
        "schedule.course.replace",
        args=[token],
        queue="schedule",
    )
    return chain(get_course, apply_adjustment, replace_course).apply_async()
