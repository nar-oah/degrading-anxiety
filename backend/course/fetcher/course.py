from datetime import date
import base64
import httpx

XLS_SIGNATURE = bytes.fromhex("D0CF11E0A1B11AE1")


class BUFTFetcher:
    def __init__(self, client: httpx.Client, base_url: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.client = client

    def login(self, user: str, password: str) -> bool:
        def get_token(value: str) -> str:
            return base64.b64encode(value.encode()).decode()

        response = self.client.post(
            f"{self.base_url}/bjgsdxjhxy_jsxsd/xk/LoginToXk",
            data={"encoded": f"{get_token(user)}%%%{get_token(password)}"},
        )
        response.raise_for_status()
        return "xsMain.jsp" in str(response.url)

    def get_excel(self, day: date) -> bytes:
        def get_semester(year: int, month: int) -> str:
            return f"{year}-{year + 1}-1" if month >= 7 else f"{year - 1}-{year}-2"

        def get_error() -> bytes:
            raise ValueError("Course system did not return an Excel timetable")

        response = self.client.post(
            f"{self.base_url}/bjgsdxjhxy_jsxsd/xskb/xskb_print.do",
            params={"xnxq01id": get_semester(day.year, day.month), "zc": ""},
        )
        response.raise_for_status()
        return (
            response.content
            if response.content.startswith(XLS_SIGNATURE)
            else get_error()
        )
