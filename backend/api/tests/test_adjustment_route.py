from datetime import date
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import call, patch
from fastapi.testclient import TestClient
import main
import tasks


class AdjustmentRouteTest(TestCase):
    def test_adjustment_route_accepts_pdf_and_course_date(self) -> None:
        result = SimpleNamespace(id="adjustment-task-id")
        with patch.object(main, "add_adjustment_task", return_value=result) as add:
            response = TestClient(main.app).post(
                "/adjustment",
                params={"token": "token", "date": "2026-09-14"},
                files={"file": ("notice.pdf", b"pdf", "application/pdf")},
            )

        self.assertEqual(response.status_code, 202)
        self.assertEqual(response.json(), "adjustment-task-id")
        add.assert_called_once_with("token", date(2026, 9, 14), b"pdf")

    def test_adjustment_route_rejects_non_monday(self) -> None:
        response = TestClient(main.app).post(
            "/adjustment",
            params={"token": "token", "date": "2026-09-15"},
            files={"file": ("notice.pdf", b"pdf", "application/pdf")},
        )

        self.assertEqual(response.status_code, 400)


class AdjustmentTaskTest(TestCase):
    def test_adjustment_chain_routes_each_worker(self) -> None:
        result = SimpleNamespace(id="adjustment-task-id")
        with (
            patch.object(tasks.celery_app, "signature", side_effect=["get", "apply", "replace"])
            as signature,
            patch.object(tasks, "chain") as add_chain,
        ):
            add_chain.return_value.apply_async.return_value = result
            task = tasks.add_adjustment_task("token", date(2026, 9, 14), b"pdf")

        self.assertEqual(task, result)
        self.assertEqual(
            signature.call_args_list,
            [
                call("course.get", args=[{"date": "2026-09-14"}], queue="course"),
                call("adjustment.apply", args=[b"pdf"], queue="adjustment"),
                call("schedule.course.replace", args=["token"], queue="schedule"),
            ],
        )
        add_chain.assert_called_once_with("get", "apply", "replace")
