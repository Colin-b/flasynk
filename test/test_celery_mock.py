import celery
import flask
from flask_testing import TestCase

import flasynk.celery_mock


class CeleryMockTest(TestCase):
    def create_app(self):
        celery_app = flasynk.celery_mock.CeleryMock(
            celery.Celery(
                "celery_server",
                broker="memory://localhost/",
                backend="memory://localhost/",
                namespace="pycommon_test-test",
                include="pycommon_test.test.test",
            )
        )

        @celery_app.task(queue=celery_app.namespace)
        def method_to_call(param1, *args, **kwargs):
            return {"param1": param1, "args": args, **kwargs}

        @celery_app.task(queue=celery_app.namespace)
        def method_with_exception():
            raise Exception("Exception in Celery task")

        app = flask.Flask(__name__)

        @app.route("/test_celery_sync")
        def test_celery_sync():
            return flask.jsonify(method_to_call(1, "a", "b", c="c1", d="d1"))

        @app.route("/test_celery_async")
        def test_celery_async():
            celery_task = method_to_call.apply_async(
                args=(1, "a", "b"), kwargs={"c": "c1", "d": "d1"}
            )
            return flask.jsonify({"id": celery_task.id})

        @app.route("/test_celery_async_with_exception")
        def test_celery_async_with_exception():
            try:
                celery_task = method_with_exception.apply_async()
                celery_result = celery.result.AsyncResult(
                    celery_task.id, app=celery_app
                )
            except Exception:
                raise Exception("This exception should not be raised")
            return celery_result.get(propagate=True)

        app.testing = True
        return app

    def test_celery_task_call_sync(self):
        response = self.client.get("/test_celery_sync")
        self.assert_200(response)
        self.assertDictEqual(
            response.json, {"args": ["a", "b"], "c": "c1", "d": "d1", "param1": 1}
        )

    def test_celery_task_call_async(self):
        response = self.client.get("/test_celery_async")
        self.assert_200(response)
        self.assertRegex(f"{response.json}", "{'id': '.*-.*-.*-.*-.*'}")

    def test_celery_task_call_async_with_exception(self):
        with self.assertRaises(Exception) as exception:
            self.client.get("/test_celery_async_with_exception")

        self.assertEqual(str(exception.exception), "Exception in Celery task")
