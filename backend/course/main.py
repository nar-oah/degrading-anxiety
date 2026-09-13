from os import environ, getenv
from celery import Celery
import httpx
from degrading_anxiety_contracts.schedule import CourseRequest, REventList
from fetcher.course import BUFTFetcher
from parser.course import ClassParser

celery_app = Celery(
    "course_worker",
    broker="redis://redis:6379/0",
    backend="redis://redis:6379/1",
)
BASE_URL = "http://jw.bjbuft.edu.cn"


@celery_app.task(
    name="course.get",
    pydantic=True,
    pydantic_strict=False,
)
def get_course(request: CourseRequest) -> REventList:
    with httpx.Client(follow_redirects=True, timeout=30) as client:
        fetcher = BUFTFetcher(client, getenv("COURSE_BASE_URL", BASE_URL))
        assert fetcher.login(
            environ["COURSE_USER"], environ["COURSE_PASSWORD"]
        ), "Course system login failed"
        events = ClassParser(fetcher.get_excel(request.date), request.date).get_parse()
        return REventList(root=list(events))
