from typing import Union

import flask_testing


class TestCase(flask_testing.TestCase):
    def assert_202_regex(self, response, expected_location_regex: str) -> str:
        """
        Assert that status code is 202.
        202 stands for Accepted, meaning that location header is expected as well.
        Assert that location header is containing the expected location (hostname trimmed for tests)

        :param response: response object from service to be asserted
        :param expected_location_regex: Expected location starting from server root (eg: /xxx). Can be a regular exp.
        :return Location from server root.
        """
        self.assertStatus(response, 202)
        actual_location = response.headers["location"].replace("http://localhost", "")
        self.assertRegex(actual_location, expected_location_regex)
        return actual_location

    def assert_303_regex(self, response, expected_location_regex: str) -> str:
        """
        Assert that status code is 303.
        303 stands for See Other, meaning that location header is expected as well.
        Assert that location header is containing the expected location (hostname trimmed for tests)

        :param response: response object from service to be asserted
        :param expected_location_regex: Expected location starting from server root (eg: /xxx). Can be a regular exp.
        :return Location from server root.
        """
        self.assertStatus(response, 303)
        actual_location = response.location.replace("http://localhost", "")
        self.assertRegex(actual_location, expected_location_regex)
        return actual_location

    def assert_text(self, response, expected: str):
        """
        Assert that response is containing the following text.

        :param response: Received query response.
        :param expected: Expected text.
        """
        self.assertEqual(expected, _to_text(response.data))


def _to_text(body: Union[bytes, str]) -> str:
    return body if isinstance(body, str) else body.decode("utf-8")
