from collections.abc import Callable
from alloc import Alloc
from radicale import ALLOC_CALENDAR, Radicale
from pathlib import Path
import bcrypt
import fcntl
from degrading_anxiety_contracts.schedule import Task, Arrange, REvent

CALENDAR = "schedule"
USERS_FILE = Path("/auth/users")


def add_schedule(radicale: Radicale, tasks: list[Task]) -> None:
    def get_event(task: Task, alloc: Alloc) -> REvent:
        dtstart, dtend = alloc.get_schedule(task.duration, task.arrange)
        return REvent(
            summary=task.description,
            dtstart=dtstart,
            dtend=dtend,
            description=task.description,
            alarms=[0] if task.arrange == Arrange.NORMAL else [15],
        )

    def add_event(event: REvent) -> None:
        radicale.add_event(ALLOC_CALENDAR, event)

    alloc = Alloc(radicale)
    list(map(lambda task: add_event(get_event(task, alloc)), tasks))


def add_user(token: str) -> Radicale:
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
        write_user(file) if not has_user(file) else False
        radicale = Radicale(token)
        fcntl.flock(file, fcntl.LOCK_UN)
        return radicale


if __name__ == "__main__":
    tasks = [
        Task(description="test", duration=10),
        Task(description="test2", duration=20),
    ]
    add_schedule(Radicale("test"), tasks)
