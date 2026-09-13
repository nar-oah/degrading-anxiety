from datetime import date, datetime
from enum import Enum
from pydantic import BaseModel, Field, RootModel


class Arrange(Enum):
    EARLY = "early"
    LATE = "late"
    NORMAL = "normal"


class Task(BaseModel):
    description: str
    duration: int
    arrange: Arrange = Arrange.NORMAL


class TaskList(RootModel[list[Task]]):
    pass


class REvent(BaseModel):
    summary: str
    dtstart: datetime
    dtend: datetime
    location: str = ""
    description: str = ""
    alarms: list[int] = Field(default_factory=lambda: [15])
    repeat: tuple[int, int] | None = None


class REventList(RootModel[list[REvent]]):
    pass


class CourseRequest(BaseModel):
    date: date
