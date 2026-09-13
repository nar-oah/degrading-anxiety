from datetime import datetime
from unittest import TestCase
from unittest.mock import patch
import main
from degrading_anxiety_contracts.schedule import REvent


class ExamWorkerTest(TestCase):
    def test_course_user_selects_student(self) -> None:
        event = REvent(
            summary="金融风险管理",
            dtstart=datetime(2026, 9, 17, 10, 10),
            dtend=datetime(2026, 9, 17, 11, 50),
        )
        with (
            patch.dict(main.environ, {"COURSE_USER": "23131116"}),
            patch.object(main, "ExamParser") as parser,
        ):
            parser.return_value.get_exam.return_value = iter((event,))
            result = main.get_exam.run(b"excel")

        parser.assert_called_once_with(b"excel")
        parser.return_value.get_exam.assert_called_once_with(23131116)
        self.assertEqual(result.root, [event])
