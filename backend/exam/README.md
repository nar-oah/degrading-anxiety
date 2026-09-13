# Exam worker

The exam worker parses an uploaded `.xls` or `.xlsx` exam schedule, selects the
courses belonging to the student identified by `COURSE_USER`, and sends calendar
events to the schedule worker through Celery.

Configure the same numeric teaching-system user used by the course worker:

```dotenv
COURSE_USER=23131116
```
