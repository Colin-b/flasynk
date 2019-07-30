import unittest.mock as mock
import os

import pytest
from flask import Flask, make_response
from flask_restplus import Api, Resource, fields

import flasynk
import flasynk.celery_specifics
import flasynk.celery_mock


class DateTimeMock:
    @staticmethod
    def utcnow():
        class UTCDateTimeMock:
            @staticmethod
            def isoformat():
                return "2018-10-11T15:05:05.663979"

        return UTCDateTimeMock


@pytest.fixture
def app():
    application = Flask(__name__)
    application.testing = True

    api = Api(application)
    config = {
        "celery": {"broker": "memory://localhost/", "backend": "memory://localhost/"}
    }
    celery_application = flasynk.celery_mock.CeleryMock(
        flasynk.celery_specifics.build_async_application(config)
    )

    ns = flasynk.AsyncNamespaceProxy(
        api.namespace("Test space", path="/foo", description="Test"), celery_application
    )

    @ns.asynchronous_route(
        "/bar",
        serializer=api.model(
            "BarModel", {"status": fields.String, "foo": fields.String}
        ),
    )
    class TestEndpoint(Resource):
        @ns.doc(**ns.how_to_get_asynchronous_status_doc)
        def get(self):
            @celery_application.task(queue=celery_application.namespace)
            def fetch_the_answer():
                return {"status": "why not", "foo": "bar"}

            celery_task = fetch_the_answer.apply_async()
            return flasynk.how_to_get_asynchronous_status(celery_task)

    @ns.asynchronous_route(
        "/bar2",
        [api.model("Bar2Model", {"status2": fields.String, "foo2": fields.String})],
    )
    class TestEndpoint2(Resource):
        @ns.doc(**ns.how_to_get_asynchronous_status_doc)
        def get(self):
            @celery_application.task(queue=celery_application.namespace)
            def fetch_the_answer():
                return [{"status2": "why not2", "foo2": "bar2"}]

            celery_task = fetch_the_answer.apply_async()
            return flasynk.how_to_get_asynchronous_status(celery_task)

    def modify_response(task_result: int) -> int:
        return task_result * 2

    @ns.asynchronous_route("/modified_task_result", to_response=modify_response)
    class TestEndpointModifiedTaskResult(Resource):
        @ns.doc(**ns.how_to_get_asynchronous_status_doc)
        def get(self):
            @celery_application.task(queue=celery_application.namespace)
            def fetch_the_answer():
                return 3

            celery_task = fetch_the_answer.apply_async()
            return flasynk.how_to_get_asynchronous_status(celery_task)

    @ns.asynchronous_route("/exception", to_response=modify_response)
    class TestEndpointException(Resource):
        @ns.doc(**ns.how_to_get_asynchronous_status_doc)
        def get(self):
            @celery_application.task(queue=celery_application.namespace)
            def fetch_the_answer():
                raise Exception("Celery task exception")

            celery_task = fetch_the_answer.apply_async()
            return flasynk.how_to_get_asynchronous_status(celery_task)

    @ns.asynchronous_route("/csv")
    class TestEndpointNoSerialization(Resource):
        @ns.doc(**ns.how_to_get_asynchronous_status_doc)
        def get(self):
            @celery_application.task(queue=celery_application.namespace)
            def fetch_the_answer():
                return make_response("a;b;c", 200, {"Content-type": "text/csv"})

            celery_task = fetch_the_answer.apply_async()
            return flasynk.how_to_get_asynchronous_status(celery_task)

    def to_path_response(result, str_value, int_value):
        return make_response(
            f"{str_value}: {result * int_value}", 200, {"Content-type": "text/plain"}
        )

    @ns.asynchronous_route(
        "/path_parameters/<string:str_value>/<int:int_value>",
        to_response=to_path_response,
    )
    class TestEndpointWithPathParameter(Resource):
        @ns.doc(**ns.how_to_get_asynchronous_status_doc)
        def get(self, str_value, int_value):
            @celery_application.task(queue=celery_application.namespace)
            def fetch_the_answer():
                return 3

            celery_task = fetch_the_answer.apply_async()
            return flasynk.how_to_get_asynchronous_status(celery_task)

    return application


@mock.patch.dict(os.environ, {"HOSTNAME": "my_host", "CONTAINER_NAME": "/v1.2.3"})
def test_health_details_with_workers(client, monkeypatch):
    monkeypatch.setattr(flasynk.celery_specifics, "datetime", DateTimeMock)
    from celery.task import control

    control.ping = lambda destination: [
        {worker: {"pong": "ok"}} for worker in destination
    ]
    status, details = flasynk.celery_specifics.health_details()
    assert status == "pass"
    assert details == {
        "celery:ping": {
            "componentType": "component",
            "observedValue": [{"celery@/v1.2.3_my_host": {"pong": "ok"}}],
            "status": "pass",
            "time": "2018-10-11T15:05:05.663979",
        }
    }


@mock.patch.dict(os.environ, {"HOSTNAME": "my_host", "CONTAINER_NAME": "/v1.2.3"})
def test_health_details_without_workers(client, monkeypatch):
    monkeypatch.setattr(flasynk.celery_specifics, "datetime", DateTimeMock)
    from celery.task import control

    control.ping = lambda destination: []
    status, details = flasynk.celery_specifics.health_details()
    assert status == "fail"
    assert details == {
        "celery:ping": {
            "componentType": "component",
            "output": "No celery@/v1.2.3_my_host workers could be found.",
            "status": "fail",
            "time": "2018-10-11T15:05:05.663979",
        }
    }


@mock.patch.dict(os.environ, {"HOSTNAME": "my_host", "CONTAINER_NAME": "/v1.2.3"})
def test_health_details_ping_exception(client, monkeypatch):
    monkeypatch.setattr(flasynk.celery_specifics, "datetime", DateTimeMock)
    from celery.task import control

    def ex(destination):
        raise Exception(f"{destination} ping failure")

    control.ping = ex
    status, details = flasynk.celery_specifics.health_details()
    assert status == "fail"
    assert details == {
        "celery:ping": {
            "componentType": "component",
            "output": "['celery@/v1.2.3_my_host'] ping failure",
            "status": "fail",
            "time": "2018-10-11T15:05:05.663979",
        }
    }
