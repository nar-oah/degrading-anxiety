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
    def get_login(fetcher: BUFTFetcher) -> BUFTFetcher:
        def get_error() -> BUFTFetcher:
            raise PermissionError("Course system login failed")

        logged_in = fetcher.get_login(
            environ["COURSE_USER"],
            environ["COURSE_PASSWORD"],
        )
        return fetcher if logged_in else get_error()

    with httpx.Client(follow_redirects=True, timeout=30) as client:
        fetcher = get_login(
            BUFTFetcher(client, getenv("COURSE_BASE_URL", BASE_URL))
        )
        events = ClassParser(fetcher.get_excel(request.date), request.date).get_parse()
        return REventList(root=list(events))
