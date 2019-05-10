# -*- coding: utf-8 -*-

import datetime
import logging
import uuid

import celery.result
from celery import states

logger = logging.getLogger(__name__)


def _serialize(value):
    if isinstance(value, datetime.datetime):
        return value.isoformat()
    if isinstance(value, dict):
        return {key: _serialize(key_value) for key, key_value in value.items()}
    if isinstance(value, list):
        return [_serialize(list_value) for list_value in value]
    if isinstance(value, tuple):
        return (_serialize(tuple_value) for tuple_value in value)
    if isinstance(value, set):
        return {_serialize(set_value) for set_value in value}
    return value


def _async_result_stub(task_id, **kwargs):
    return _TaskResultStore.get_by_id(task_id)


# apply_async returns an EagerResult in eager mode.
# To ensure it always returns an EagerResult even when AsyncResult is called, we use this mock
celery.result.AsyncResult = _async_result_stub


class _EagerResultWithStateSupport(celery.result.EagerResult):
    def ready(self):
        return self._state == states.READY_STATES


class _TaskResultStore:

    __task_store = {}

    @classmethod
    def put(cls, result):
        cls.__task_store[result.id] = result

    @classmethod
    def get_by_id(cls, id):
        return (
            cls.__task_store[id]
            if id in cls.__task_store
            else _EagerResultWithStateSupport(id, None, states.PENDING)
        )


class CeleryMock:
    """
    Celery App proxy. This proxy configures celery app in "task always eager" mode.
    This proxy intercepts task decorator so apply_async is working in this mode.
    """

    def __init__(self, celery_app):
        self.__celery_app = celery_app
        self.__celery_app.conf.update(
            task_always_eager=True,
            result_backend="cache",
            cache_backend="memory",
            task_eager_propagates=True,
        )
        self.__task_store = {}

    def __getattr__(self, name):
        if name == "task":

            def task_interceptor(*aa, **oo):
                result = getattr(self.__celery_app, "task")(*aa, **oo)

                class AsyncTaskProxy:
                    def __init__(self, method, *a, **o):
                        self.__method = method

                    def apply_async(
                        self,
                        args=None,
                        kwargs=None,
                        task_id=None,
                        producer=None,
                        link=None,
                        link_error=None,
                        shadow=None,
                        **options,
                    ):
                        serialized_args = (
                            [_serialize(arg) for arg in args] if args else ()
                        )
                        serialized_kwargs = (
                            {name: _serialize(value) for name, value in kwargs.items()}
                            if kwargs
                            else {}
                        )

                        task_id = task_id if task_id else str(uuid.uuid4())

                        try:
                            method_result = self.__method(
                                *serialized_args, **serialized_kwargs
                            )
                            celery_result = celery.result.EagerResult(
                                task_id, method_result, states.SUCCESS
                            )
                        except Exception as e:
                            celery_result = celery.result.EagerResult(
                                task_id, e, states.FAILURE
                            )

                        _TaskResultStore.put(celery_result)
                        return celery_result

                    def __call__(self, *args, **kwargs):
                        return self.__method(*args, **kwargs)

                return AsyncTaskProxy

            return task_interceptor
        else:
            return getattr(self.__celery_app, name)
