from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import call, patch
import main
import tasks
from fastapi.testclient import TestClient


class ExamRouteTest(TestCase):
    def test_exam_route_accepts_excel_upload(self) -> None:
        result = SimpleNamespace(id="exam-task-id")
        with patch.object(main, "add_exam_task", return_value=result) as add_exam:
            response = TestClient(main.app).post(
                "/exam",
                params={"token": "token"},
                files={"file": ("exam.xls", b"excel", "application/vnd.ms-excel")},
            )

        self.assertEqual(response.status_code, 202)
        self.assertEqual(response.json(), "exam-task-id")
        add_exam.assert_called_once_with("token", b"excel")


class ExamTaskTest(TestCase):
    def test_exam_chain_routes_each_worker(self) -> None:
        result = SimpleNamespace(id="exam-task-id")
        with (
            patch.object(tasks.celery_app, "signature", side_effect=["get", "add"])
            as signature,
            patch.object(tasks, "chain") as add_chain,
        ):
            add_chain.return_value.apply_async.return_value = result
            task = tasks.add_exam_task("token", b"excel")

        self.assertEqual(task, result)
        self.assertEqual(
            signature.call_args_list,
            [
                call("exam.get", args=[b"excel"], queue="exam"),
                call("schedule.exam", args=["token"], queue="schedule"),
            ],
        )
        add_chain.assert_called_once_with("get", "add")
