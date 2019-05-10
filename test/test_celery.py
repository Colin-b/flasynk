import unittest.mock as mock
import os
import datetime

import flask
from flask import Flask, make_response
from flask_restplus import Api, Resource, fields
from test.enhanced_flask_testing import TestCase

import flasynk
import flasynk.celery_specifics
import flasynk.celery_mock


class UTCDateTimeMock:
    @staticmethod
    def isoformat():
        return "2018-10-11T15:05:05.663979"


class AsyncRouteTest(TestCase):
    def create_app(self):
        app = Flask(__name__)
        app.config["TESTING"] = True
        app.config["DEBUG"] = True

        self.api = Api(app)
        config = {
            "celery": {
                "broker": "memory://localhost/",
                "backend": "memory://localhost/",
            }
        }
        celery_application = flasynk.celery_mock.CeleryMock(
            flasynk.celery_specifics.build_async_application(config)
        )

        ns = flasynk.AsyncNamespaceProxy(
            self.api.namespace("Test space", path="/foo", description="Test"),
            celery_application,
        )

        @ns.asynchronous_route(
            "/bar",
            serializer=self.api.model(
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
            [
                self.api.model(
                    "Bar2Model", {"status2": fields.String, "foo2": fields.String}
                )
            ],
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

        def to_csv_response(result):
            return make_response(result, 200, {"Content-type": "text/csv"})

        @ns.asynchronous_route("/csv", to_response=to_csv_response)
        class TestEndpointNoSerialization(Resource):
            @ns.doc(**ns.how_to_get_asynchronous_status_doc)
            def get(self):
                @celery_application.task(queue=celery_application.namespace)
                def fetch_the_answer():
                    return "a;b;c"

                celery_task = fetch_the_answer.apply_async()
                return flasynk.how_to_get_asynchronous_status(celery_task)

        def to_path_response(result, str_value, int_value):
            return make_response(
                f"{str_value}: {result * int_value}",
                200,
                {"Content-type": "text/plain"},
            )

        @ns.asynchronous_route(
            "/path_parameters/<string:str_value>/<int:int_value>",
            to_response=to_path_response,
        )
        class TestEndpointWithPathParameter(Resource):
            @ns.doc(**ns.how_to_get_asynchronous_status_doc)
            def get(self, str_value, int_value):
                @celery_application.task(queue=celery_application.namespace)
                def fetch_the_answer(d, l, s, t, dt):
                    return 3

                celery_task = fetch_the_answer.apply_async(
                    args=(dict(), list(), set(), tuple(), datetime.datetime.utcnow())
                )
                return flasynk.how_to_get_asynchronous_status(celery_task)

        return app

    def test_async_ns_proxy_creates_2_extra_endpoints_per_declared_endpoint(self):
        response = self.client.get("/swagger.json")
        self.assert_200(response)
        self.assertDictEqual(
            response.json,
            {
                "swagger": "2.0",
                "basePath": "/",
                "paths": {
                    "/foo/bar": {
                        "get": {
                            "responses": {
                                "202": {
                                    "description": "Computation started.",
                                    "schema": {
                                        "$ref": "#/definitions/AsyncTaskStatusModel"
                                    },
                                    "headers": {
                                        "location": {
                                            "description": "URL to fetch computation status from.",
                                            "type": "string",
                                        }
                                    },
                                }
                            },
                            "operationId": "get_test_endpoint",
                            "tags": ["Test space"],
                        }
                    },
                    "/foo/bar/result/{task_id}": {
                        "parameters": [
                            {
                                "name": "task_id",
                                "in": "path",
                                "required": True,
                                "type": "string",
                            }
                        ],
                        "get": {
                            "responses": {
                                "200": {
                                    "description": "Success",
                                    "schema": {"$ref": "#/definitions/BarModel"},
                                }
                            },
                            "summary": "Retrieve result for provided task",
                            "operationId": "get_test_endpoint_result",
                            "parameters": [
                                {
                                    "name": "X-Fields",
                                    "in": "header",
                                    "type": "string",
                                    "format": "mask",
                                    "description": "An optional fields mask",
                                }
                            ],
                            "tags": ["Test space"],
                        },
                    },
                    "/foo/bar/status/{task_id}": {
                        "parameters": [
                            {
                                "name": "task_id",
                                "in": "path",
                                "required": True,
                                "type": "string",
                            }
                        ],
                        "get": {
                            "responses": {
                                "200": {
                                    "description": "Task is still computing.",
                                    "schema": {
                                        "$ref": "#/definitions/CurrentAsyncState"
                                    },
                                },
                                "303": {
                                    "description": "Result is available.",
                                    "headers": {
                                        "location": {
                                            "description": "URL to fetch results from.",
                                            "type": "string",
                                        }
                                    },
                                },
                                "500": {
                                    "description": "An unexpected error occurred.",
                                    "schema": {
                                        "type": "string",
                                        "description": "Stack trace.",
                                    },
                                },
                            },
                            "summary": "Retrieve status for provided task",
                            "operationId": "get_test_endpoint_status",
                            "tags": ["Test space"],
                        },
                    },
                    "/foo/bar2": {
                        "get": {
                            "responses": {
                                "202": {
                                    "description": "Computation started.",
                                    "schema": {
                                        "$ref": "#/definitions/AsyncTaskStatusModel"
                                    },
                                    "headers": {
                                        "location": {
                                            "description": "URL to fetch computation status from.",
                                            "type": "string",
                                        }
                                    },
                                }
                            },
                            "operationId": "get_test_endpoint2",
                            "tags": ["Test space"],
                        }
                    },
                    "/foo/bar2/result/{task_id}": {
                        "parameters": [
                            {
                                "name": "task_id",
                                "in": "path",
                                "required": True,
                                "type": "string",
                            }
                        ],
                        "get": {
                            "responses": {
                                "200": {
                                    "description": "Success",
                                    "schema": {
                                        "type": "array",
                                        "items": {"$ref": "#/definitions/Bar2Model"},
                                    },
                                }
                            },
                            "summary": "Retrieve result for provided task",
                            "operationId": "get_test_endpoint2_result",
                            "parameters": [
                                {
                                    "name": "X-Fields",
                                    "in": "header",
                                    "type": "string",
                                    "format": "mask",
                                    "description": "An optional fields mask",
                                }
                            ],
                            "tags": ["Test space"],
                        },
                    },
                    "/foo/bar2/status/{task_id}": {
                        "parameters": [
                            {
                                "name": "task_id",
                                "in": "path",
                                "required": True,
                                "type": "string",
                            }
                        ],
                        "get": {
                            "responses": {
                                "200": {
                                    "description": "Task is still computing.",
                                    "schema": {
                                        "$ref": "#/definitions/CurrentAsyncState"
                                    },
                                },
                                "303": {
                                    "description": "Result is available.",
                                    "headers": {
                                        "location": {
                                            "description": "URL to fetch results from.",
                                            "type": "string",
                                        }
                                    },
                                },
                                "500": {
                                    "description": "An unexpected error occurred.",
                                    "schema": {
                                        "type": "string",
                                        "description": "Stack trace.",
                                    },
                                },
                            },
                            "summary": "Retrieve status for provided task",
                            "operationId": "get_test_endpoint2_status",
                            "tags": ["Test space"],
                        },
                    },
                    "/foo/csv": {
                        "get": {
                            "responses": {
                                "202": {
                                    "description": "Computation started.",
                                    "schema": {
                                        "$ref": "#/definitions/AsyncTaskStatusModel"
                                    },
                                    "headers": {
                                        "location": {
                                            "description": "URL to fetch computation status from.",
                                            "type": "string",
                                        }
                                    },
                                }
                            },
                            "operationId": "get_test_endpoint_no_serialization",
                            "tags": ["Test space"],
                        }
                    },
                    "/foo/csv/result/{task_id}": {
                        "parameters": [
                            {
                                "name": "task_id",
                                "in": "path",
                                "required": True,
                                "type": "string",
                            }
                        ],
                        "get": {
                            "responses": {"200": {"description": "Success"}},
                            "summary": "Retrieve result for provided task",
                            "operationId": "get_test_endpoint_no_serialization_result",
                            "tags": ["Test space"],
                        },
                    },
                    "/foo/csv/status/{task_id}": {
                        "parameters": [
                            {
                                "name": "task_id",
                                "in": "path",
                                "required": True,
                                "type": "string",
                            }
                        ],
                        "get": {
                            "responses": {
                                "200": {
                                    "description": "Task is still computing.",
                                    "schema": {
                                        "$ref": "#/definitions/CurrentAsyncState"
                                    },
                                },
                                "303": {
                                    "description": "Result is available.",
                                    "headers": {
                                        "location": {
                                            "description": "URL to fetch results from.",
                                            "type": "string",
                                        }
                                    },
                                },
                                "500": {
                                    "description": "An unexpected error occurred.",
                                    "schema": {
                                        "type": "string",
                                        "description": "Stack trace.",
                                    },
                                },
                            },
                            "summary": "Retrieve status for provided task",
                            "operationId": "get_test_endpoint_no_serialization_status",
                            "tags": ["Test space"],
                        },
                    },
                    "/foo/exception": {
                        "get": {
                            "responses": {
                                "202": {
                                    "description": "Computation started.",
                                    "schema": {
                                        "$ref": "#/definitions/AsyncTaskStatusModel"
                                    },
                                    "headers": {
                                        "location": {
                                            "description": "URL to fetch computation status from.",
                                            "type": "string",
                                        }
                                    },
                                }
                            },
                            "operationId": "get_test_endpoint_exception",
                            "tags": ["Test space"],
                        }
                    },
                    "/foo/exception/result/{task_id}": {
                        "parameters": [
                            {
                                "name": "task_id",
                                "in": "path",
                                "required": True,
                                "type": "string",
                            }
                        ],
                        "get": {
                            "responses": {"200": {"description": "Success"}},
                            "summary": "Retrieve result for provided task",
                            "operationId": "get_test_endpoint_exception_result",
                            "tags": ["Test space"],
                        },
                    },
                    "/foo/exception/status/{task_id}": {
                        "parameters": [
                            {
                                "name": "task_id",
                                "in": "path",
                                "required": True,
                                "type": "string",
                            }
                        ],
                        "get": {
                            "responses": {
                                "200": {
                                    "description": "Task is still computing.",
                                    "schema": {
                                        "$ref": "#/definitions/CurrentAsyncState"
                                    },
                                },
                                "303": {
                                    "description": "Result is available.",
                                    "headers": {
                                        "location": {
                                            "description": "URL to fetch results from.",
                                            "type": "string",
                                        }
                                    },
                                },
                                "500": {
                                    "description": "An unexpected error occurred.",
                                    "schema": {
                                        "type": "string",
                                        "description": "Stack trace.",
                                    },
                                },
                            },
                            "summary": "Retrieve status for provided task",
                            "operationId": "get_test_endpoint_exception_status",
                            "tags": ["Test space"],
                        },
                    },
                    "/foo/modified_task_result": {
                        "get": {
                            "responses": {
                                "202": {
                                    "description": "Computation started.",
                                    "schema": {
                                        "$ref": "#/definitions/AsyncTaskStatusModel"
                                    },
                                    "headers": {
                                        "location": {
                                            "description": "URL to fetch computation status from.",
                                            "type": "string",
                                        }
                                    },
                                }
                            },
                            "operationId": "get_test_endpoint_modified_task_result",
                            "tags": ["Test space"],
                        }
                    },
                    "/foo/modified_task_result/result/{task_id}": {
                        "parameters": [
                            {
                                "name": "task_id",
                                "in": "path",
                                "required": True,
                                "type": "string",
                            }
                        ],
                        "get": {
                            "responses": {"200": {"description": "Success"}},
                            "summary": "Retrieve result for provided task",
                            "operationId": "get_test_endpoint_modified_task_result_result",
                            "tags": ["Test space"],
                        },
                    },
                    "/foo/modified_task_result/status/{task_id}": {
                        "parameters": [
                            {
                                "name": "task_id",
                                "in": "path",
                                "required": True,
                                "type": "string",
                            }
                        ],
                        "get": {
                            "responses": {
                                "200": {
                                    "description": "Task is still computing.",
                                    "schema": {
                                        "$ref": "#/definitions/CurrentAsyncState"
                                    },
                                },
                                "303": {
                                    "description": "Result is available.",
                                    "headers": {
                                        "location": {
                                            "description": "URL to fetch results from.",
                                            "type": "string",
                                        }
                                    },
                                },
                                "500": {
                                    "description": "An unexpected error occurred.",
                                    "schema": {
                                        "type": "string",
                                        "description": "Stack trace.",
                                    },
                                },
                            },
                            "summary": "Retrieve status for provided task",
                            "operationId": "get_test_endpoint_modified_task_result_status",
                            "tags": ["Test space"],
                        },
                    },
                    "/foo/path_parameters/{str_value}/{int_value}": {
                        "parameters": [
                            {
                                "name": "str_value",
                                "in": "path",
                                "required": True,
                                "type": "string",
                            },
                            {
                                "name": "int_value",
                                "in": "path",
                                "required": True,
                                "type": "integer",
                            },
                        ],
                        "get": {
                            "responses": {
                                "202": {
                                    "description": "Computation started.",
                                    "schema": {
                                        "$ref": "#/definitions/AsyncTaskStatusModel"
                                    },
                                    "headers": {
                                        "location": {
                                            "description": "URL to fetch computation status from.",
                                            "type": "string",
                                        }
                                    },
                                }
                            },
                            "operationId": "get_test_endpoint_with_path_parameter",
                            "tags": ["Test space"],
                        },
                    },
                    "/foo/path_parameters/{str_value}/{int_value}/result/{task_id}": {
                        "parameters": [
                            {
                                "name": "str_value",
                                "in": "path",
                                "required": True,
                                "type": "string",
                            },
                            {
                                "name": "int_value",
                                "in": "path",
                                "required": True,
                                "type": "integer",
                            },
                            {
                                "name": "task_id",
                                "in": "path",
                                "required": True,
                                "type": "string",
                            },
                        ],
                        "get": {
                            "responses": {"200": {"description": "Success"}},
                            "summary": "Retrieve result for provided task",
                            "operationId": "get_test_endpoint_with_path_parameter_result",
                            "tags": ["Test space"],
                        },
                    },
                    "/foo/path_parameters/{str_value}/{int_value}/status/{task_id}": {
                        "parameters": [
                            {
                                "name": "str_value",
                                "in": "path",
                                "required": True,
                                "type": "string",
                            },
                            {
                                "name": "int_value",
                                "in": "path",
                                "required": True,
                                "type": "integer",
                            },
                            {
                                "name": "task_id",
                                "in": "path",
                                "required": True,
                                "type": "string",
                            },
                        ],
                        "get": {
                            "responses": {
                                "200": {
                                    "description": "Task is still computing.",
                                    "schema": {
                                        "$ref": "#/definitions/CurrentAsyncState"
                                    },
                                },
                                "303": {
                                    "description": "Result is available.",
                                    "headers": {
                                        "location": {
                                            "description": "URL to fetch results from.",
                                            "type": "string",
                                        }
                                    },
                                },
                                "500": {
                                    "description": "An unexpected error occurred.",
                                    "schema": {
                                        "type": "string",
                                        "description": "Stack trace.",
                                    },
                                },
                            },
                            "summary": "Retrieve status for provided task",
                            "operationId": "get_test_endpoint_with_path_parameter_status",
                            "tags": ["Test space"],
                        },
                    },
                },
                "info": {"title": "API", "version": "1.0"},
                "produces": ["application/json"],
                "consumes": ["application/json"],
                "tags": [{"name": "Test space", "description": "Test"}],
                "definitions": {
                    "AsyncTaskStatusModel": {
                        "required": ["task_id", "url"],
                        "properties": {
                            "task_id": {"type": "string", "description": "Task Id."},
                            "url": {
                                "type": "string",
                                "description": "URL when task status can be checked.",
                            },
                        },
                        "type": "object",
                    },
                    "BarModel": {
                        "properties": {
                            "status": {"type": "string"},
                            "foo": {"type": "string"},
                        },
                        "type": "object",
                    },
                    "CurrentAsyncState": {
                        "required": ["state"],
                        "properties": {
                            "state": {
                                "type": "string",
                                "description": "Indicates current computation state.",
                                "example": "PENDING",
                            }
                        },
                        "type": "object",
                    },
                    "Bar2Model": {
                        "properties": {
                            "status2": {"type": "string"},
                            "foo2": {"type": "string"},
                        },
                        "type": "object",
                    },
                },
                "responses": {
                    "ParseError": {"description": "When a mask can't be parsed"},
                    "MaskError": {"description": "When any error occurs on mask"},
                },
            },
        )

    def test_async_call_task(self):
        response = self.client.get("/foo/bar")
        status_url = self.assert_202_regex(response, "/foo/bar/status/.*")
        self.assertRegex(response.json["url"], "http://localhost/foo/bar/status/.*")
        status_reply = self.client.get(status_url)
        result_url = self.assert_303_regex(status_reply, "/foo/bar/result/.*")
        result_reply = self.client.get(result_url)
        self.assert_200(result_reply)
        self.assertDictEqual(result_reply.json, {"status": "why not", "foo": "bar"})

        response = self.client.get("/foo/bar2")
        status_url = self.assert_202_regex(response, "/foo/bar2/status/.*")
        self.assertRegex(response.json["url"], "http://localhost/foo/bar2/status/.*")
        status_reply = self.client.get(status_url)
        result_url = self.assert_303_regex(status_reply, "/foo/bar2/result/.*")
        result_reply = self.client.get(result_url)
        self.assert_200(result_reply)
        self.assertListEqual(
            result_reply.json, [{"status2": "why not2", "foo2": "bar2"}]
        )

    def test_async_call_task_without_huey(self):
        class FailHuey:
            def __getattr__(self, item):
                raise ModuleNotFoundError()

        import huey

        previous_api = huey.api
        huey.api = FailHuey()
        response = self.client.get("/foo/bar")
        status_url = self.assert_202_regex(response, "/foo/bar/status/.*")
        self.assertRegex(response.json["url"], "http://localhost/foo/bar/status/.*")
        status_reply = self.client.get(status_url)
        result_url = self.assert_303_regex(status_reply, "/foo/bar/result/.*")
        result_reply = self.client.get(result_url)
        self.assert_200(result_reply)
        self.assertDictEqual(result_reply.json, {"status": "why not", "foo": "bar"})

        response = self.client.get("/foo/bar2")
        status_url = self.assert_202_regex(response, "/foo/bar2/status/.*")
        self.assertRegex(response.json["url"], "http://localhost/foo/bar2/status/.*")
        status_reply = self.client.get(status_url)
        result_url = self.assert_303_regex(status_reply, "/foo/bar2/result/.*")
        result_reply = self.client.get(result_url)
        self.assert_200(result_reply)
        self.assertListEqual(
            result_reply.json, [{"status2": "why not2", "foo2": "bar2"}]
        )
        huey.api = previous_api

    def test_async_call_task_without_endpoint_call(self):
        status_reply = self.client.get("/foo/bar/status/42")
        self.assert_200(status_reply)
        self.assertDictEqual(status_reply.json, {"state": "PENDING"})

    def test_async_call_with_modified_response(self):
        response = self.client.get("/foo/modified_task_result")
        status_url = self.assert_202_regex(
            response, "/foo/modified_task_result/status/.*"
        )
        status_reply = self.client.get(status_url)
        result_url = self.assert_303_regex(
            status_reply, "/foo/modified_task_result/result/.*"
        )
        result_reply = self.client.get(result_url)
        self.assert_200(result_reply)
        self.assert_text(result_reply, "6\n")

    def test_async_call_with_path_parameters_and_modified_response(self):
        response = self.client.get("/foo/path_parameters/test/2")
        status_url = self.assert_202_regex(
            response, "/foo/path_parameters/test/2/status/.*"
        )
        status_reply = self.client.get(status_url)
        result_url = self.assert_303_regex(
            status_reply, "/foo/path_parameters/test/2/result/.*"
        )
        result_reply = self.client.get(result_url)
        self.assert_200(result_reply)
        self.assert_text(result_reply, "test: 6")

    def test_exception_raised_and_propagated(self):
        response = self.client.get("/foo/exception")
        status_url = self.assert_202_regex(response, ".*")
        status_reply = self.client.get(status_url)
        result_url = self.assert_303_regex(status_reply, ".*")
        self.assert_500(self.client.get(result_url))

    def test_async_call_without_serialization(self):
        response = self.client.get("/foo/csv")
        status_url = self.assert_202_regex(response, "/foo/csv/status/.*")
        self.assertRegex(response.json["url"], "http://localhost/foo/csv/status/.*")
        status_reply = self.client.get(status_url)
        result_url = self.assert_303_regex(status_reply, "/foo/csv/result/.*")
        result_reply = self.client.get(result_url)
        self.assert_200(result_reply)
        self.assertEqual(result_reply.data.decode(), "a;b;c")

    @mock.patch("flasynk.celery_specifics.datetime")
    @mock.patch.dict(os.environ, {"HOSTNAME": "my_host"})
    def test_health_details_with_workers(self, datetime_mock):
        datetime_mock.utcnow = mock.Mock(return_value=UTCDateTimeMock)
        from celery.task import control

        control.ping = lambda destination: [
            {worker: {"pong": "ok"}} for worker in destination
        ]
        status, details = flasynk.celery_specifics.health_details()
        self.assertEqual(status, "pass")
        self.assertEqual(
            details,
            {
                "celery:ping": {
                    "componentType": "component",
                    "observedValue": [{"celery@local_my_host": {"pong": "ok"}}],
                    "status": "pass",
                    "time": "2018-10-11T15:05:05.663979",
                }
            },
        )

    @mock.patch("flasynk.celery_specifics.datetime")
    @mock.patch.dict(os.environ, {"HOSTNAME": "my_host"})
    def test_health_details_without_workers(self, datetime_mock):
        datetime_mock.utcnow = mock.Mock(return_value=UTCDateTimeMock)
        from celery.task import control

        control.ping = lambda destination: []
        status, details = flasynk.celery_specifics.health_details()
        self.assertEqual(status, "fail")
        self.assertEqual(
            details,
            {
                "celery:ping": {
                    "componentType": "component",
                    "output": "No celery@local_my_host workers could be found.",
                    "status": "fail",
                    "time": "2018-10-11T15:05:05.663979",
                }
            },
        )

    @mock.patch("flasynk.celery_specifics.datetime")
    @mock.patch.dict(os.environ, {"HOSTNAME": "my_host"})
    def test_health_details_ping_exception(self, datetime_mock):
        datetime_mock.utcnow = mock.Mock(return_value=UTCDateTimeMock)
        from celery.task import control

        def ex(destination=None):
            raise Exception(f"{destination} ping failure")

        control.ping = ex
        status, details = flasynk.celery_specifics.health_details()
        self.assertEqual(status, "fail")
        self.assertEqual(
            details,
            {
                "celery:ping": {
                    "componentType": "component",
                    "output": "['celery@local_my_host'] ping failure",
                    "status": "fail",
                    "time": "2018-10-11T15:05:05.663979",
                }
            },
        )


class RedisAndCeleryHealthTest(TestCase):
    def create_app(self):
        app = Flask(__name__)
        app.config["TESTING"] = True
        app.config["DEBUG"] = True

        self.api = Api(app)
        config = {
            "celery": {
                "broker": "memory://localhost/",
                "backend": "memory://localhost/",
            }
        }
        celery_application = flasynk.celery_mock.CeleryMock(
            flasynk.celery_specifics.build_async_application(config)
        )

        ns = flasynk.AsyncNamespaceProxy(
            self.api.namespace("Test space", path="/foo", description="Test"),
            celery_application,
        )

        @ns.asynchronous_route(
            "/bar",
            serializer=self.api.model(
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
            [
                self.api.model(
                    "Bar2Model", {"status2": fields.String, "foo2": fields.String}
                )
            ],
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
                f"{str_value}: {result * int_value}",
                200,
                {"Content-type": "text/plain"},
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

        return app

    @mock.patch("flasynk.celery_specifics.datetime")
    @mock.patch.dict(os.environ, {"HOSTNAME": "my_host", "CONTAINER_NAME": "/v1.2.3"})
    def test_health_details_with_workers(self, datetime_mock):
        datetime_mock.utcnow = mock.Mock(return_value=UTCDateTimeMock)
        from celery.task import control

        control.ping = lambda destination: [
            {worker: {"pong": "ok"}} for worker in destination
        ]
        status, details = flasynk.celery_specifics.health_details()
        self.assertEqual(status, "pass")
        self.assertEqual(
            details,
            {
                "celery:ping": {
                    "componentType": "component",
                    "observedValue": [{"celery@/v1.2.3_my_host": {"pong": "ok"}}],
                    "status": "pass",
                    "time": "2018-10-11T15:05:05.663979",
                }
            },
        )

    @mock.patch("flasynk.celery_specifics.datetime")
    @mock.patch.dict(os.environ, {"HOSTNAME": "my_host", "CONTAINER_NAME": "/v1.2.3"})
    def test_health_details_without_workers(self, datetime_mock):
        datetime_mock.utcnow = mock.Mock(return_value=UTCDateTimeMock)
        from celery.task import control

        control.ping = lambda destination: []
        status, details = flasynk.celery_specifics.health_details()
        self.assertEqual(status, "fail")
        self.assertEqual(
            details,
            {
                "celery:ping": {
                    "componentType": "component",
                    "output": "No celery@/v1.2.3_my_host workers could be found.",
                    "status": "fail",
                    "time": "2018-10-11T15:05:05.663979",
                }
            },
        )

    @mock.patch("flasynk.celery_specifics.datetime")
    @mock.patch.dict(os.environ, {"HOSTNAME": "my_host", "CONTAINER_NAME": "/v1.2.3"})
    def test_health_details_ping_exception(self, datetime_mock):
        datetime_mock.utcnow = mock.Mock(return_value=UTCDateTimeMock)
        from celery.task import control

        def ex(destination):
            raise Exception(f"{destination} ping failure")

        control.ping = ex
        status, details = flasynk.celery_specifics.health_details()
        self.assertEqual(status, "fail")
        self.assertEqual(
            details,
            {
                "celery:ping": {
                    "componentType": "component",
                    "output": "['celery@/v1.2.3_my_host'] ping failure",
                    "status": "fail",
                    "time": "2018-10-11T15:05:05.663979",
                }
            },
        )


class TestGetCeleryStatus(TestCase):
    def create_app(self):
        app = Flask(__name__)
        app.config["TESTING"] = True
        return app

    def test_get_async_status(self):
        class CeleryTaskStub:
            id = "idtest"

        celery_task = CeleryTaskStub()
        flask.request.base_url = "http://localhost/foo"
        response = flasynk.how_to_get_asynchronous_status(celery_task)
        self.assert_202_regex(response, "/foo/status/idtest")
        self.assertDictEqual(
            response.json,
            {"task_id": "idtest", "url": "http://localhost/foo/status/idtest"},
        )
