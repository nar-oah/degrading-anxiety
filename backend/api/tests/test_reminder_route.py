from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import patch
from fastapi.testclient import TestClient
import main
import tasks


class ReminderRouteTest(TestCase):
    def test_reminder_enqueues_old_and_new_minutes(self) -> None:
        with patch.object(tasks.celery_app, "send_task", return_value=SimpleNamespace(id="task-id")) as send:
            response = TestClient(main.app).post(
                "/reminder", params={"token": "token", "old_minutes": 15, "new_minutes": 30}
            )

        self.assertEqual(response.status_code, 202)
        self.assertEqual(response.json(), "task-id")
        send.assert_called_once_with("schedule.reminder", args=["token", 15, 30], queue="schedule")

    def test_reminder_accepts_zero(self) -> None:
        with patch.object(main, "add_task", return_value=SimpleNamespace(id="task-id")) as add:
            response = TestClient(main.app).post(
                "/reminder", params={"token": "token", "old_minutes": 15, "new_minutes": 0}
            )

        self.assertEqual(response.status_code, 202)
        add.assert_called_once_with("schedule.reminder", "token", 15, 0)

    def test_reminder_rejects_negative_or_noninteger_values(self) -> None:
        for parameter in ("old_minutes", "new_minutes"):
            for value in (-1, "1.5", "invalid"):
                with self.subTest(parameter=parameter, value=value), patch.object(main, "add_task") as add:
                    params = {"token": "token", "old_minutes": 15, "new_minutes": 30}
                    params[parameter] = value
                    response = TestClient(main.app).post("/reminder", params=params)
                    self.assertEqual(response.status_code, 400)
                    add.assert_not_called()

    def test_creation_routes_reject_invalid_reminders_before_enqueuing(self) -> None:
        for path in ("/course", "/course/sync", "/exam", "/adjustment", "/alloc"):
            for minutes in (-1, "1.5"):
                with (
                    self.subTest(path=path, minutes=minutes),
                    patch.object(tasks.celery_app, "signature") as signature,
                    patch.object(tasks.celery_app, "send_task") as send,
                ):
                    upload = {"file": ("import.pdf", b"content")} if path in ("/exam", "/adjustment") else None
                    response = TestClient(main.app).post(
                        path,
                        params={"token": "token", "date": "2026-09-14", "reminder_minutes": minutes},
                        files=upload,
                        json=[] if path == "/alloc" else None,
                    )
                    self.assertEqual(response.status_code, 400)
                    signature.assert_not_called()
                    send.assert_not_called()


class AllocRouteTest(TestCase):
    def test_alloc_forwards_default_and_custom_reminders_with_serialized_tasks(self) -> None:
        for minutes in (None, 30, 0):
            with self.subTest(minutes=minutes), patch.object(
                tasks.celery_app, "send_task", return_value=SimpleNamespace(id="task-id")
            ) as send:
                params = {"token": "token"}
                if minutes is not None:
                    params["reminder_minutes"] = minutes
                response = TestClient(main.app).post("/alloc", params=params, json=[
                    {"description": "task", "duration": 10, "arrange": "early"}
                ])
                self.assertEqual(response.status_code, 202)
                send.assert_called_once_with(
                    "schedule.alloc",
                    args=["token", [{"description": "task", "duration": 10, "arrange": "early"}],
                          15 if minutes is None else minutes],
                    queue="schedule",
                )
