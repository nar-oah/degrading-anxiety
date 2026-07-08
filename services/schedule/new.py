from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from alloc import Alloc
from radicale import REvent, Radicale
from pathlib import Path
import bcrypt
import fcntl

CALENDAR = "schedule"
USERS_FILE = Path("/etc/radicale/users")
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

    def add_event(event: REvent) -> None:
        radicale.add_event(CALENDAR, event)

    alloc = Alloc()
    list(map(lambda task: add_event(get_event(task, alloc)), tasks))


def add_user(token: str) -> None:
    def get_login(line: str) -> str:
        return line.split(":", 1)[0]

    def has_user(file) -> bool:
        file.seek(0)
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
        write_user(file) if not has_user(file) else None
        Radicale(token).add_calendar(CALENDAR)
        fcntl.flock(file, fcntl.LOCK_UN)


if __name__ == "__main__":
    add_schedule([Task("test", 10), Task("test2", 20)])
