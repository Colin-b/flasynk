import json
import logging
import re
from urllib.parse import urlparse

import flask
from flask_restplus import Resource, fields, Namespace


logger = logging.getLogger("asynchronous_server")

_STATUS_ENDPOINT = "status"
_RESULT_ENDPOINT = "result"


class AsyncNamespaceProxy:
    """
    Flask rest-plus Namespace proxy.
    This proxy namespace add a decorator 'async_route' that will generate 2 extra endpoint : /status and /result
    to query the status or the result of the huey task
    """

    def __init__(self, namespace: Namespace, async_app):
        self.__namespace = namespace
        self.__async_app = async_app
        task_status_model = namespace.model(
            "AsyncTaskStatusModel",
            {
                "task_id": fields.String(required=True, description="Task Id."),
                "url": fields.String(
                    required=True, description="URL when task status can be checked."
                ),
            },
        )
        self.how_to_get_asynchronous_status_doc = {
            "responses": {
                202: (
                    "Computation started.",
                    task_status_model,
                    {"headers": {"location": "URL to fetch computation status from."}},
                )
            }
        }

    def __getattr__(self, name):
        return getattr(self.__namespace, name)

    def asynchronous_route(self, endpoint: str, serializer=None, to_response=None):
        """
        Add an async route endpoint.
        :param endpoint: value of the exposes endpoint ex: /foo
        :param serializer: In case the response needs serialization, a single model or a list of model.
        If a list is given, the output will be treated (serialized) and documented as a list
        :param to_response: In case the task result needs to be processed before returning it to client.
        This is a function taking the task result as parameter (and path parameters if needed) and returning a result.
        Default to returning unmodified task result.
        :return: route decorator
        """

        def wrapper(cls):
            # Create the requested route
            self.__namespace.route(endpoint)(cls)
            # Create two additional endpoints to retrieve status and result
            _build_result_endpoints(
                cls.__name__,
                endpoint,
                self.__namespace,
                self.__async_app,
                serializer,
                to_response,
            )
            return cls

        return wrapper


def _base_url() -> str:
    """
    Return client original requested URL in order to make sure it works behind a reverse proxy as well.
    Without parameters.
    """
    if "X-Original-Request-Uri" in flask.request.headers:
        parsed = urlparse(flask.request.headers["X-Original-Request-Uri"])
        return f'{flask.request.scheme}://{flask.request.headers["Host"]}{parsed.path}'
    return flask.request.base_url


def how_to_get_asynchronous_status(async_task) -> flask.Response:
    url = f"{_base_url()}/{_STATUS_ENDPOINT}/{async_task.id}"
    status = flask.Response()
    status.status_code = 202
    status.content_type = "application/json"
    status.headers["location"] = url
    status.data = json.dumps({"task_id": async_task.id, "url": url})
    return status


def _get_asynchronous_status(async_task_id: str, async_app) -> flask.Response:
    async_module = _module(async_app)
    async_task = async_module._get_asynchronous_task(async_task_id, async_app)
    if async_module._result_is_available(async_task):
        status = flask.Response()
        status.status_code = 303
        status.headers["location"] = _base_url().replace(
            f"/{_STATUS_ENDPOINT}/", f"/{_RESULT_ENDPOINT}/"
        )
        return status

    # TODO Add more information such as request initial time, and maybe intermediate client status
    return flask.jsonify({"state": async_module._get_current_state(async_task)})


def _build_result_endpoints(
    base_class,
    endpoint_root: str,
    namespace: Namespace,
    async_app,
    response_model,
    to_response: callable,
):
    @namespace.route(f"{endpoint_root}/{_RESULT_ENDPOINT}/<string:task_id>")
    class AsyncTaskResult(Resource):
        @_conditional_marshalling(namespace, response_model)
        @namespace.doc(f"get_{_snake_case(base_class)}_result")
        def get(self, task_id: str, **kwargs):
            """
            Retrieve result for provided task.
            """
            result = _module(async_app)._get_asynchronous_result(async_app, task_id)
            return to_response(result, **kwargs) if to_response else result

    @namespace.route(f"{endpoint_root}/{_STATUS_ENDPOINT}/<string:task_id>")
    @namespace.doc(
        responses={
            200: (
                "Task is still computing.",
                namespace.model(
                    "CurrentAsyncState",
                    {
                        "state": fields.String(
                            description="Indicates current computation state.",
                            required=True,
                            example="PENDING",
                        )
                    },
                ),
            ),
            303: (
                "Result is available.",
                None,
                {"headers": {"location": "URL to fetch results from."}},
            ),
            500: (
                "An unexpected error occurred.",
                fields.String(description="Stack trace.", required=True),
            ),
        }
    )
    class AsyncTaskStatus(Resource):
        @namespace.doc(f"get_{_snake_case(base_class)}_status")
        def get(self, task_id: str, **kwargs):
            """
            Retrieve status for provided task.
            """
            return _get_asynchronous_status(task_id, async_app)


def _conditional_marshalling(namespace: Namespace, response_model):
    def wrapper(func):
        if response_model is not None:
            return namespace.marshal_with(
                response_model[0]
                if isinstance(response_model, list)
                else response_model,
                as_list=isinstance(response_model, list),
            )(func)
        return func

    return wrapper


def _snake_case(name: str) -> str:
    if "_" in name:
        raise ValueError(f"{name} should be Camel Case and should not contain any _")
    s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
    return re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1).lower()


def _module(async_app):
    try:
        import huey

        if isinstance(async_app, huey.api.Huey):
            import flasynk.huey_specifics

            return flasynk.huey_specifics
    except ModuleNotFoundError:
        pass  # If huey cannot be imported then it means Celery is used
    import flasynk.celery_specifics

    return flasynk.celery_specifics
