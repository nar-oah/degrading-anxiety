from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from alloc import Alloc
from radicale import REvent, Radicale
from pathlib import Path
import bcrypt
import fcntl

CALENDAR = "schedule"
USERS_FILE = Path("/auth/users")


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
    description: str
    duration: int
    arrange: Arrange = Arrange.NORMAL


def add_schedule(radicale: Radicale, tasks: list[Task]) -> None:
    def get_event(task: Task, alloc: Alloc) -> REvent:
        return REvent(
            task.description,
            *alloc.get_schedule(task.duration, task.arrange.key),
            description=task.description,
            alarms=[0] if task.arrange == Arrange.NORMAL else [15],
        )

    def add_event(event: REvent) -> None:
        radicale.add_event(event)

    alloc = Alloc(radicale)
    list(map(lambda task: add_event(get_event(task, alloc)), tasks))


def add_user(token: str) -> None:
    def has_user(file) -> bool:
        file.seek(0)
        get_login: Callable[[str], str] = lambda line: line.split(":", 1)[0]
        return token in map(get_login, filter(lambda line: ":" in line, file))

    def write_user(file) -> bool:
        password = bcrypt.hashpw(token.encode("utf-8"), bcrypt.gensalt()).decode(
            "utf-8"
        )
        file.seek(0, 2)
        file.write(f"{token}:{password}\n")
        file.flush()
        return True

    with USERS_FILE.open("a+", encoding="utf-8") as file:
        fcntl.flock(file, fcntl.LOCK_EX)
        if not has_user(file):
            write_user(file)
            Radicale(token).add_calendar()
        fcntl.flock(file, fcntl.LOCK_UN)


if __name__ == "__main__":
    add_schedule(Radicale("test"), [Task("test", 10), Task("test2", 20)])
