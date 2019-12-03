import re


def assert_202_regex(response, expected_location_regex: str) -> str:
    """
    Assert that status code is 202.
    202 stands for Accepted, meaning that location header is expected as well.
    Assert that location header is containing the expected location (hostname trimmed for tests)

    :param response: response object from service to be asserted
    :param expected_location_regex: Expected location starting from server root (eg: /xxx). Can be a regular exp.
    :return Location from server root.
    """
    assert response.status_code == 202
    actual_location = response.headers["location"].replace("http://localhost", "")
    assert re.match(expected_location_regex, actual_location)
    return actual_location


def assert_303_regex(response, expected_location_regex: str) -> str:
    """
    Assert that status code is 303.
    303 stands for See Other, meaning that location header is expected as well.
    Assert that location header is containing the expected location (hostname trimmed for tests)

    :param response: response object from service to be asserted
    :param expected_location_regex: Expected location starting from server root (eg: /xxx). Can be a regular exp.
    :return Location from server root.
    """
    assert response.status_code == 303
    actual_location = response.location.replace("http://localhost", "")
    assert re.match(expected_location_regex, actual_location)
    return actual_location
