from datetime import date
from unittest import TestCase
from unittest.mock import patch
import main
import pandas as pd


class CourseWorkerTest(TestCase):
    def test_import_uses_default_or_requested_reminder(self) -> None:
        frame = pd.DataFrame(index=range(9), columns=range(8))
        frame.iloc[1, 1] = "数学◇张老师◇◇1-2([周])[01-02节]◇M1-101"
        for requested in (None, 30, 0):
            with (
                self.subTest(reminder_minutes=requested),
                patch.dict(
                    main.environ, {"COURSE_USER": "user", "COURSE_PASSWORD": "pwd"}
                ),
                patch.object(main, "BUFTFetcher") as fetcher,
                patch.object(main.httpx, "Client"),
                patch("parser.course.pd.read_excel", return_value=frame),
            ):
                fetcher.return_value.get_login.return_value = True
                fetcher.return_value.get_excel.return_value = b"excel"
                kwargs = {} if requested is None else {"reminder_minutes": requested}
                events = main.get_course.run({"date": "2026-09-14"}, **kwargs)

                self.assertEqual(len(events), 1)
                self.assertEqual(
                    events[0]["alarms"], [15 if requested is None else requested]
                )
                self.assertEqual(events[0]["repeat"], [2, 1])
                fetcher.return_value.get_excel.assert_called_once_with(
                    date(2026, 9, 14)
                )
