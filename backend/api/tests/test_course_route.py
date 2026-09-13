from datetime import date
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import call, patch
import main
import tasks
from fastapi import HTTPException


class CourseRouteTest(TestCase):
    def test_course_route_returns_chain_id(self) -> None:
        result = SimpleNamespace(id="course-task-id")
        with patch.object(main, "add_course_task", return_value=result) as add_course:
            task_id = main.add_course("token", date(2026, 9, 14))

        self.assertEqual(task_id, "course-task-id")
        add_course.assert_called_once_with("token", date(2026, 9, 14))

    def test_course_route_rejects_non_monday(self) -> None:
        with self.assertRaises(HTTPException) as raised:
            main.add_course("token", date(2026, 9, 15))

        self.assertEqual(raised.exception.status_code, 400)

    def test_course_chain_routes_each_worker(self) -> None:
        result = SimpleNamespace(id="course-task-id")
        with (
            patch.object(tasks.celery_app, "signature", side_effect=["fetch", "add"]) as signature,
            patch.object(tasks, "chain") as add_chain,
        ):
            add_chain.return_value.apply_async.return_value = result
            task = tasks.add_course_task("token", date(2026, 9, 14))

        self.assertEqual(task, result)
        self.assertEqual(
            signature.call_args_list,
            [
                call(
                    "course.get",
                    args=[{"date": "2026-09-14"}],
                    queue="course",
                ),
                call("schedule.course", args=["token"], queue="schedule"),
            ],
        )
        add_chain.assert_called_once_with("fetch", "add")
