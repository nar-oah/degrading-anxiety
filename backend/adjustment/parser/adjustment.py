from datetime import date
from io import BytesIO
import re
import unicodedata
from pypdf import PdfReader

DAY = r"(?:\d{4}年)?(\d{1,2})月(\d{1,2})日(?:\([^)]*\))?"
HOLIDAY = re.compile(DAY + "至" + DAY + "放假(?:调休)?")
MAKEUP = re.compile(DAY + "补" + DAY)
YEAR = re.compile(r"(?<!\d)(\d{4})年")


def get_adjustment(pdf: bytes) -> tuple[list[tuple[date, date]], list[tuple[date, date]]]:
    pages = PdfReader(BytesIO(pdf)).pages
    raw = "".join(map(lambda page: page.extract_text() or "", pages))
    text = "".join(unicodedata.normalize("NFKC", raw).split())
    if not text:
        raise ValueError("Scanned PDF is not supported: no text could be extracted")

    found_year = YEAR.search(text)
    if found_year is None:
        raise ValueError("No year found in PDF text")

    year = int(found_year.group(1))

    def get_dates(match: re.Match[str]) -> tuple[date, date]:
        first_month, first_day, second_month, second_day = map(int, match.groups())
        return date(year, first_month, first_day), date(year, second_month, second_day)

    holidays = list(map(get_dates, HOLIDAY.finditer(text)))
    makeups = list(map(get_dates, MAKEUP.finditer(text)))
    if not holidays and not makeups:
        raise ValueError("No holiday or makeup rules found in PDF text")
    return holidays, makeups
