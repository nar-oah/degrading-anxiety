# Adjustment service

The `adjustment` Celery worker accepts `adjustment.apply(events, pdf)`, where
`events` is the latest `REventList` from `course.get` and `pdf` contains a
text-based academic calendar notice. It returns the complete adjusted
`REventList` for `schedule.course.replace`.

The parser normalizes extracted text with NFKC, removes whitespace, and reads
the year and holiday/makeup dates from the PDF body. Recurring course events
are expanded into dated events before holidays are removed. Makeup dates copy
courses from the original expanded timetable, including courses whose source
date falls within a holiday. Each copied event keeps its course details and
changes only its date.

Image-only or scanned PDFs with no extractable text are rejected. OCR is not
used.
