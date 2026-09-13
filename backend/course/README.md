# Course worker

The course worker logs in to the teaching system, downloads the timetable Excel
file, converts its rows to calendar events, and returns them to the schedule
worker through Celery.

Configure the worker through the deployment `.env` file:

```dotenv
COURSE_USER=your-teaching-system-user
COURSE_PASSWORD=your-teaching-system-password
COURSE_BASE_URL=http://jw.bjbuft.edu.cn
```

`COURSE_BASE_URL` is optional. The submitted date anchors the earliest teaching
week present in the timetable.
