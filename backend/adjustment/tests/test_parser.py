from datetime import date
from unittest import TestCase
from unittest.mock import patch
from parser.adjustment import get_adjustment


class AdjustmentParserTest(TestCase):
    def get_rules(self, text: str) -> tuple[list[tuple[date, date]], list[tuple[date, date]]]:
        with patch("parser.adjustment.PdfReader") as reader:
            reader.return_value.pages = [reader.return_value]
            reader.return_value.extract_text.return_value = text
            return get_adjustment(b"pdf")

    def test_fullwidth_text_and_spaces_are_normalized(self) -> None:
        holidays, makeups = self.get_rules(
            "关于 ２０２６ 年放假通知\n"
            "９ 月 ２５ 日（周五） 至 １０ 月 ７ 日（周三） 放假调休。\n"
            "９ 月 ２０ 日（周日） 补 １０ 月 ５ 日（第６周周一）的课程。"
        )

        self.assertEqual(holidays, [(date(2026, 9, 25), date(2026, 10, 7))])
        self.assertEqual(makeups, [(date(2026, 9, 20), date(2026, 10, 5))])

    def test_explicit_date_years_override_document_year(self) -> None:
        holidays, _ = self.get_rules(
            "2026 年通知: 2026年12月31日至2027年1月2日放假。"
        )
        self.assertEqual(holidays, [(date(2026, 12, 31), date(2027, 1, 2))])

    def test_scanned_pdf_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "Scanned PDF"):
            self.get_rules("   \n")
