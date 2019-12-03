import flask
import pytest

import flasynk


@pytest.fixture
def app():
    application = flask.Flask(__name__)
    application.testing = True

    @application.route("/test_get_async_status")
    def get_async_status():
        class CeleryTaskStub:
            id = "idtest"

        celery_task = CeleryTaskStub()
        return flasynk.how_to_get_asynchronous_status(celery_task)

    return application


def test_get_async_status(client):
    response = client.get("/test_get_async_status")
    assert response.status_code == 202
    assert (
        response.headers["location"]
        == "http://localhost/test_get_async_status/status/idtest"
    )
    assert response.json == {
        "task_id": "idtest",
        "url": "http://localhost/test_get_async_status/status/idtest",
    }
