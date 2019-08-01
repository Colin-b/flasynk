import pytest


@pytest.fixture
def mock_huey(huey_app_func):
    def proxify(func):
        def wrapper(*args, **kwargs):
            huey_app = func(*args, **kwargs)
            huey_app.immediate = True
            return huey_app

        return wrapper

    return proxify(huey_app_func)
