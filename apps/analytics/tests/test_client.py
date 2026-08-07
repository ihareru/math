from django.test import RequestFactory, SimpleTestCase

from apps.analytics.services.client import (
    detect_device_type,
    get_client_ip,
    parse_browser,
    parse_operating_system,
)


class ClientParserTests(SimpleTestCase):
    def test_firefox_is_detected(self):
        browser, version = parse_browser(
            (
                "Mozilla/5.0 "
                "(Windows NT 10.0; Win64; x64) "
                "Gecko/20100101 Firefox/153.0"
            )
        )

        self.assertEqual(browser, "Firefox")
        self.assertEqual(version, "153.0")

    def test_chrome_is_detected(self):
        browser, version = parse_browser(
            (
                "Mozilla/5.0 "
                "(Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 "
                "Chrome/141.0.0.0 Safari/537.36"
            )
        )

        self.assertEqual(browser, "Chrome")
        self.assertEqual(version, "141.0.0.0")

    def test_windows_is_detected(self):
        operating_system = (
            parse_operating_system(
                "Mozilla/5.0 (Windows NT 10.0)"
            )
        )

        self.assertEqual(
            operating_system,
            "Windows 10/11",
        )

    def test_mobile_is_detected(self):
        device_type = detect_device_type(
            (
                "Mozilla/5.0 "
                "(Linux; Android 15; Mobile)"
            )
        )

        self.assertEqual(
            device_type,
            "mobile",
        )

    def test_remote_address_is_used(self):
        factory = RequestFactory()

        request = factory.get(
            "/",
            REMOTE_ADDR="127.0.0.1",
        )

        self.assertEqual(
            get_client_ip(request),
            "127.0.0.1",
        )