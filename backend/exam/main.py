from os import environ
from celery import Celery
from degrading_anxiety_contracts.schedule import REventList
from parser.exam import ExamParser

celery_app = Celery(
    "exam_worker",
    broker="redis://redis:6379/0",
    backend="redis://redis:6379/1",
)


@celery_app.task(
    name="exam.get",
    pydantic=True,
    pydantic_strict=False,
)
def get_exam(excel: bytes) -> REventList:
    student_id = int(environ["COURSE_USER"])
    return REventList(root=list(ExamParser(excel).get_exam(student_id)))
