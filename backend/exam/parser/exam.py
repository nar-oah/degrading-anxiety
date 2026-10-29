from collections.abc import Hashable, Iterable
from datetime import date, datetime, time
from io import BytesIO
from itertools import chain
import logging
from numbers import Real
import re
from unicodedata import normalize
import pandas as pd
from openpyxl.utils.datetime import MAC_EPOCH, WINDOWS_EPOCH, from_excel
from degrading_anxiety_contracts.schedule import REvent


logger = logging.getLogger(__name__)


def is_missing(value: object) -> bool:
    return bool(pd.isna(value)) or (
        isinstance(value, str) and value.strip() in ("", "无", "无辅导", "无考试")
    )


def parse_date(value: object, epoch: datetime) -> date:
    if is_missing(value):
        raise ValueError("Missing date")
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, Real) and not isinstance(value, bool):
        result = from_excel(float(value), epoch=epoch)
        if isinstance(result, datetime):
            return result.date()
    if isinstance(value, str):
        return datetime.fromisoformat(value.strip()).date()
    raise ValueError("Invalid date")


def parse_time(value: object) -> time:
    if is_missing(value):
        raise ValueError("Missing time")
    if isinstance(value, datetime):
        return value.time()
    if isinstance(value, time):
        return value
    if isinstance(value, Real) and not isinstance(value, bool):
        number = float(value)
        if 0 <= number < 1:
            return from_excel(number)
        if number.is_integer() and 0 <= number < 24:
            return time(int(number))
    if isinstance(value, str):
        text = normalize("NFKC", value).strip().replace(";", ":")
        match = re.search(r"(?<!\d)(\d{1,2}):(\d{1,2})(?::(\d{1,2}))?(?!\d)", text)
        if match is None:
            match = re.search(r"(?<!\d)(\d{1,2})[点时](?:(\d{1,2})分?)?", text)
        if match is None:
            match = re.fullmatch(r"(\d{1,2})", text)
        if match is not None:
            parts = match.groups()
            hour = int(parts[0])
            minute = int(parts[1] or 0) if len(parts) > 1 else 0
            second = int(parts[2] or 0) if len(parts) > 2 else 0
            if any(period in text for period in ("下午", "晚上", "晚")) and hour < 12:
                hour += 12
            elif any(period in text for period in ("上午", "凌晨")) and hour == 12:
                hour = 0
            return time(hour, minute, second)
    raise ValueError("Invalid time")


def get_column(data: pd.DataFrame | pd.Series, text: str) -> str | None:
    return next(filter(lambda value: text in str(value), data.keys()), None)


class ExamParser:
    def __init__(self, excel_bytes: bytes, reminder_minutes: int = 15) -> None:
        self.reminder_minutes = reminder_minutes

        def get_sheets(excel: pd.ExcelFile, texts: tuple[str, ...]) -> Iterable[pd.DataFrame]:
            def get_sheet(name: str) -> pd.DataFrame:
                return pd.read_excel(excel, sheet_name=name, skiprows=1)

            def get_match(sheet: pd.DataFrame) -> bool:
                return all(
                    map(
                        lambda text: isinstance(get_column(sheet, text), str),
                        texts,
                    )
                )

            return filter(get_match, map(get_sheet, excel.sheet_names))

        with pd.ExcelFile(BytesIO(excel_bytes)) as excel:
            self.epoch = getattr(
                excel.book, "epoch",
                MAC_EPOCH if getattr(excel.book, "datemode", 0) else WINDOWS_EPOCH,
            )
            self.students = pd.concat(get_sheets(excel, ("学号",)), ignore_index=True)
            self.schedule = tuple(get_sheets(excel, ("课程编号", "日期")))

    def get_exam(self, student_id: int) -> Iterable[REvent]:
        def get_rows() -> Iterable[tuple[Hashable, pd.Series]]:
            student_rows = self.students[self.students["学号"] == student_id]
            course_ids: list[str] = student_rows["课程编号"].tolist()

            def get_ids(schedule: pd.DataFrame) -> pd.Series:
                return schedule.loc[:, get_column(schedule, "课程编号")].isin(
                    course_ids
                )

            def get_date(schedule: pd.DataFrame) -> pd.Series:
                return schedule.loc[:, get_column(schedule, "日期")].map(
                    lambda value: not is_missing(value)
                )

            rows = map(
                lambda value: value[get_ids(value) & get_date(value)].iterrows(),
                self.schedule,
            )
            return chain.from_iterable(rows)

        def get_range(row: pd.Series) -> tuple[datetime, datetime]:
            day = parse_date(
                row.get(get_column(row, "日期")), getattr(self, "epoch", WINDOWS_EPOCH)
            )
            start_column = get_column(row, "开始时间")
            end_column = get_column(row, "结束时间")
            if start_column is None and end_column is None:
                period = normalize("NFKC", str(row.get(get_column(row, "时间"), "")))
                start_value, end_value = period.split("~")
            else:
                start_value, end_value = row.get(start_column), row.get(end_column)
            start = datetime.combine(day, parse_time(start_value))
            end = datetime.combine(day, parse_time(end_value))
            if end <= start:
                raise ValueError("End time must be later than start time")
            return start, end

        def get_event(row: pd.Series, start: datetime, end: datetime) -> REvent:
            def get_text(text: str) -> str:
                value = row.get(get_column(row, text), "")
                return str(value) if pd.notna(value) else ""

            return REvent(
                summary=get_text("课程名"),
                dtstart=start,
                dtend=end,
                location=get_text("地点"),
                description=get_text("备注"),
                alarms=[self.reminder_minutes],
            )

        for index, row in get_rows():
            try:
                start, end = get_range(row)
            except (ValueError, TypeError, OverflowError) as error:
                logger.warning("Skipping invalid exam schedule row %s: %s", index, error)
                continue
            yield get_event(row, start, end)
