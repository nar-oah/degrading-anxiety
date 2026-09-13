from collections.abc import Callable, Hashable, Iterable
from datetime import datetime, time
from io import BytesIO
from itertools import chain
import pandas as pd
from degrading_anxiety_contracts.schedule import REvent

type Make = Callable[[pd.DataFrame], pd.Series]


def get_column(data: pd.DataFrame | pd.Series, text: str) -> str | None:
    return next(filter(lambda value: text in str(value), data.keys()), None)


class ExamParser:
    def __init__(self, excel_bytes: bytes) -> None:
        def get_sheets(
            excel: pd.ExcelFile,
            texts: tuple[str, ...],
        ) -> Iterable[pd.DataFrame]:
            def get_sheet(name: str) -> pd.DataFrame:
                return pd.read_excel(excel, sheet_name=name, skiprows=1)

            def get_match(sheet: pd.DataFrame) -> bool:
                return all(map(lambda text: isinstance(get_column(sheet, text), str), texts))

            return filter(get_match, map(get_sheet, excel.sheet_names))

        with pd.ExcelFile(BytesIO(excel_bytes)) as excel:
            self.students = pd.concat(get_sheets(excel, ("学号",)), ignore_index=True)
            self.schedule = tuple(get_sheets(excel, ("课程编号", "日期")))

    def get_exam(self, student_id: int) -> Iterable[REvent]:
        def get_rows() -> Iterable[tuple[Hashable, pd.Series]]:
            student_rows = self.students[self.students["学号"] == student_id]
            course_ids: list[str] = student_rows["课程编号"].tolist()
            is_ids: Make = lambda schedule: schedule.loc[
                :, get_column(schedule, "课程编号")
            ].isin(course_ids)
            is_date: Make = lambda schedule: schedule.loc[
                :, get_column(schedule, "日期")
            ].ne("无")
            rows = map(
                lambda value: value[is_ids(value) & is_date(value)].iterrows(),
                self.schedule,
            )
            return chain.from_iterable(rows)

        def get_range(row: pd.Series) -> tuple[datetime, datetime]:
            def get_text(value: str) -> tuple[datetime, time, time]:
                def get_clock(text: str) -> time:
                    return time.fromisoformat(text.strip().split()[-1])

                start_text, end_text = str(
                    row.get(get_column(row, "时间"))
                ).split("~")
                return (
                    datetime.fromisoformat(value.split()[0]),
                    get_clock(start_text),
                    get_clock(end_text),
                )

            def get_dt(value: time | None) -> datetime:
                return (
                    datetime.combine(day.date(), value)
                    if isinstance(day, datetime) and isinstance(value, time)
                    else datetime.now()
                )

            day: datetime | str | None = row.get(
                get_column(row, "日期"), datetime.now()
            )
            start: time | None = row.get(get_column(row, "开始时间"), None)
            end: time | None = row.get(get_column(row, "结束时间"), None)
            day, start, end = (
                get_text(day) if isinstance(day, str) else (day, start, end)
            )
            return get_dt(start), get_dt(end)

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
            )

        return map(
            lambda value: get_event(value[1], *get_range(value[1])),
            get_rows(),
        )
