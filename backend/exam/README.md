# Exam worker

The exam worker parses an uploaded `.xls` or `.xlsx` exam schedule, selects the
courses belonging to the student identified by `COURSE_USER`, and sends calendar
events to the schedule worker through Celery.

Configure the same numeric teaching-system user used by the course worker:

```dotenv
COURSE_USER=your-numeric-student-id
```

The parser accepts Excel serial dates (using the workbook date system), native
Excel dates, ISO date strings, separate start/end columns, and the older `~`
time-range column. Clock values may be native Excel times, Excel time fractions,
whole hours, or text such as `上午10点20`, `晚8：00`, and `16；05`.
Rows marked `无`, `无辅导`, or `无考试`, and rows without dates are ignored.
Invalid dates or times and non-positive durations are skipped with a worker log
warning; they never fall back to the current time.
