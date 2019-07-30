import pytest
import flask
from flask_restplus import Api, Resource

import flasynk
import flasynk.huey_specifics


@pytest.fixture
def app():
    application = flask.Flask(__name__)
    application.testing = True
    return application


def test_underscore_in_resource_name(client, app):
    huey_application = flasynk.huey_specifics.build_async_application(
        {"asynchronous": {"broker": "redis://localhost/"}}, immediate=True
    )
    ns = flasynk.AsyncNamespaceProxy(
        Api(app).namespace("Test space", path="/foo", description="Test"),
        huey_application,
    )

    with pytest.raises(ValueError) as exception_info:

        @ns.asynchronous_route("/bar")
        class Test_Endpoint(Resource):
            def get(self):
                return

    assert (
        str(exception_info.value)
        == "Test_Endpoint should be Camel Case and should not contain any _"
    )
