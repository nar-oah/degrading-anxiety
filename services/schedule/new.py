from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from alloc import Alloc
from radicale import REvent, Radicale

radicale = Radicale()


class Arrange(Enum):
    EARLY = "early"
    LATE = "late"
    NORMAL = "normal"

    @property
    def key(self) -> Callable:
        return {
            Arrange.EARLY: lambda x: x.begin,
            Arrange.LATE: lambda x: -x.begin,
            Arrange.NORMAL: lambda x: x.end - x.begin,
        }[self]


@dataclass
class Task:
    calendar: str
    description: str
    duration: int
    arrange: Arrange = Arrange.NORMAL


def add_schedule(tasks: list[Task]) -> None:
    def get_event(task: Task, alloc: Alloc) -> REvent:
        return REvent(
            task.description,
            *alloc.get_schedule(task.duration, task.arrange.key),
            description=task.description,
            alarms=[0] if task.arrange == Arrange.NORMAL else [15],
        )

    def add_event(task: Task, event: REvent) -> None:
        radicale.add_event(task.calendar, event)

    list(map(lambda task: add_event(task, get_event(task, Alloc())), tasks))


if __name__ == "__main__":
    add_schedule([Task("test", "test", 10), Task("test", "test2", 20)])
