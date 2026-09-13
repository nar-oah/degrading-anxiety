from datetime import date
from unittest import TestCase
from unittest.mock import Mock
from fetcher.course import BUFTFetcher


class CourseFetcherTest(TestCase):
    def test_login_keeps_client_session(self) -> None:
        response = Mock(url="http://example.test/xsMain.jsp")
        client = Mock()
        client.post.return_value = response

        logged_in = BUFTFetcher(client, "http://example.test/").login("user", "password")

        self.assertTrue(logged_in)
        response.raise_for_status.assert_called_once_with()
        client.post.assert_called_once_with(
            "http://example.test/bjgsdxjhxy_jsxsd/xk/LoginToXk",
            data={"encoded": "dXNlcg==%%%cGFzc3dvcmQ="},
        )

    def test_semester_comes_from_submitted_date(self) -> None:
        response = Mock(content=b"excel")
        client = Mock()
        client.post.return_value = response

        excel = BUFTFetcher(client, "http://example.test").get_excel(date(2026, 9, 14))

        self.assertEqual(excel, b"excel")
        response.raise_for_status.assert_called_once_with()
        client.post.assert_called_once_with(
            "http://example.test/bjgsdxjhxy_jsxsd/xskb/xskb_print.do",
            params={"xnxq01id": "2026-2027-1", "zc": ""},
        )
