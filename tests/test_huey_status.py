import pytest
import flask

import flasynk


@pytest.fixture
def app():
    application = flask.Flask(__name__)
    application.testing = True

    @application.route("/test_get_async_status")
    def get_async_status():
        class HueyTaskStub:
            id = "idtest"

        huey_task = HueyTaskStub()
        return flasynk.how_to_get_asynchronous_status(huey_task)

    @application.route("/test_get_async_status_with_original_request_uri")
    def get_async_status_with_original_request_uri():
        class HueyTaskStub:
            id = "idtest"

        huey_task = HueyTaskStub()
        return flasynk.how_to_get_asynchronous_status(huey_task)

    return application


def test_get_async_status(client):
    response = client.get("/test_get_async_status")
    assert response.json == {
        "task_id": "idtest",
        "url": "http://localhost/test_get_async_status/status/idtest",
    }
    assert response.status_code == 202
    assert (
        response.headers["location"]
        == "http://localhost/test_get_async_status/status/idtest"
    )


def test_get_async_status_with_original_request_uri(client):
    response = client.get(
        "/test_get_async_status_with_original_request_uri",
        headers={
            "X-Original-Request-Uri": "http://localhost/foo",
            "Host": "initial.host",
        },
    )
    assert response.json == {
        "task_id": "idtest",
        "url": "http://initial.host/foo/status/idtest",
    }
    assert response.status_code == 202
    assert response.headers["location"] == "http://initial.host/foo/status/idtest"
