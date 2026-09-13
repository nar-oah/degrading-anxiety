from datetime import datetime, time
from unittest import TestCase
import pandas as pd
from parser.exam import ExamParser


class ExamParserTest(TestCase):
    def get_parser(self, schedule: pd.DataFrame) -> ExamParser:
        parser = ExamParser.__new__(ExamParser)
        parser.students = pd.DataFrame(
            {"学号": [23000001, 23000002], "课程编号": ["FT03P207", "OTHER"]}
        )
        parser.schedule = (schedule,)
        return parser

    def test_full_date_time_text_becomes_event(self) -> None:
        schedule = pd.DataFrame(
            {
                "课程编号": ["FT03P207", "OTHER"],
                "课程名称": ["金融风险管理", "其他课程"],
                "考试日期": ["2026-09-17", "2026-09-18"],
                "考试时间": [
                    "2026-09-17 10:10~2026-09-17 11:50",
                    "08:20~10:00",
                ],
                "考试地点": ["教室 101", "教室 102"],
                "备注": [pd.NA, ""],
            }
        )

        events = list(self.get_parser(schedule).get_exam(23000001))

        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].summary, "金融风险管理")
        self.assertEqual(events[0].dtstart, datetime(2026, 9, 17, 10, 10))
        self.assertEqual(events[0].dtend, datetime(2026, 9, 17, 11, 50))
        self.assertEqual(events[0].location, "教室 101")
        self.assertEqual(events[0].description, "")

    def test_native_date_and_time_become_event(self) -> None:
        schedule = pd.DataFrame(
            {
                "课程编号": ["FT03P207"],
                "课程名称": ["金融风险管理"],
                "日期": [datetime(2026, 9, 17)],
                "开始时间": [time(10, 10)],
                "结束时间": [time(11, 50)],
                "地点": ["教室 101"],
                "备注": ["闭卷"],
            }
        )

        event = next(self.get_parser(schedule).get_exam(23000001))

        self.assertEqual(event.dtstart, datetime(2026, 9, 17, 10, 10))
        self.assertEqual(event.dtend, datetime(2026, 9, 17, 11, 50))
        self.assertEqual(event.description, "闭卷")
