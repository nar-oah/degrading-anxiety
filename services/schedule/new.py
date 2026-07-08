from collections.abc import Callable
from datetime import date
from alloc import Alloc
from radicale import REvent, Radicale
import psycopg

radicale = Radicale()
type Task = tuple[str, str, int, str]


def add_schedule() -> None:
    def get_tasks(day: date) -> list[Task]:
        query = """
            SELECT calendar_name, schedule_description, duration_minutes, arrange_type
            FROM schedules
            WHERE %s = ANY(weekdays)
            ORDER BY
                CASE arrange_type
                    WHEN 'early' THEN 0
                    WHEN 'auto' THEN 1
                    ELSE 2
                END,
                duration_minutes DESC,
                id
        """
        with psycopg.connect() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, (day.weekday(),))
                return list(cursor.fetchall())

    def get_event(task: Task, alloc: Alloc) -> tuple[str, REvent]:
        calendar, description, duration, arrange = task
        key: Callable = (
            (lambda x: x.begin)
            if arrange == "early"
            else (lambda x: -x.begin)
            if arrange == "late"
            else (lambda x: x.end - x.begin)
        )
        event = REvent(
            description,
            *alloc.get_schedule(duration, key),
            description=description,
            alarms=[0] if arrange == "auto" else [15],
        )
        return calendar, event

    def add_event(task: Task, alloc: Alloc) -> None:
        calendar, event = get_event(task, alloc)
        radicale.add_event(calendar, event)

    alloc = Alloc()
    tasks = get_tasks(date.today())
    list(map(lambda task: add_event(task, alloc), tasks))


if __name__ == "__main__":
    add_schedule()
