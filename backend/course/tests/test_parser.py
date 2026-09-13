from datetime import date, datetime
from unittest import TestCase
from unittest.mock import patch
import pandas as pd
from parser.course import ClassParser


class CourseParserTest(TestCase):
    def get_frame(self) -> pd.DataFrame:
        frame = pd.DataFrame(index=range(9), columns=range(8))
        frame.iloc[1, 1] = "第三周课程◇教师甲◇◇3-6([周])[01-02节]◇M1-101"
        frame.iloc[1, 2] = "第五周课程◇教师乙◇◇5,7([周])[01-02节]◇M1-102"
        return frame

    def test_earliest_course_week_uses_submitted_date(self) -> None:
        with patch("parser.course.pd.read_excel", return_value=self.get_frame()):
            events = list(ClassParser(b"excel", date(2026, 9, 14)).get_parse())

        third = next(filter(lambda event: event.summary == "第三周课程", events))
        fifth = next(filter(lambda event: event.summary == "第五周课程", events))
        self.assertEqual(third.dtstart, datetime(2026, 9, 14, 8, 20))
        self.assertEqual(fifth.dtstart, datetime(2026, 9, 29, 8, 20))
        self.assertEqual(third.repeat, (4, 1))
        self.assertEqual(fifth.repeat, (2, 2))

    def test_empty_timetable_returns_no_events(self) -> None:
        frame = pd.DataFrame(index=range(9), columns=range(8))
        with patch("parser.course.pd.read_excel", return_value=frame):
            events = list(ClassParser(b"excel", date(2026, 9, 14)).get_parse())

        self.assertEqual(events, [])
