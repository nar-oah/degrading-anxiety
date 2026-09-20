from datetime import date
from celery import Celery, chain
from celery.result import AsyncResult
from pydantic import BaseModel

celery_app = Celery(
    "api",
    broker="redis://redis:6379/0",
    backend="redis://redis:6379/1",
)


def add_task(name: str, token: str, value: BaseModel | int | str) -> AsyncResult:
    arg = value.model_dump(mode="json") if isinstance(value, BaseModel) else value
    return celery_app.send_task(
        name,
        args=[token, arg],
        queue="schedule",
    )


def add_course_task(token: str, day: date) -> AsyncResult:
    get_course = celery_app.signature(
        "course.get",
        args=[{"date": day.isoformat()}],
        queue="course",
    )
    add_course = celery_app.signature(
        "schedule.course",
        args=[token],
        queue="schedule",
    )
    return chain(get_course, add_course).apply_async()


def add_exam_task(token: str, excel: bytes) -> AsyncResult:
    get_exam = celery_app.signature(
        "exam.get",
        args=[excel],
        queue="exam",
    )
    add_exam = celery_app.signature(
        "schedule.exam",
        args=[token],
        queue="schedule",
    )
    return chain(get_exam, add_exam).apply_async()


def add_adjustment_task(token: str, day: date, pdf: bytes) -> AsyncResult:
    get_course = celery_app.signature(
        "course.get",
        args=[{"date": day.isoformat()}],
        queue="course",
    )
    apply_adjustment = celery_app.signature(
        "adjustment.apply",
        args=[pdf],
        queue="adjustment",
    )
    replace_course = celery_app.signature(
        "schedule.course.replace",
        args=[token],
        queue="schedule",
    )
    return chain(get_course, apply_adjustment, replace_course).apply_async()
