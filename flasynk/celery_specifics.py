from datetime import datetime
import logging
import os

import celery.result
from celery import Celery
from celery.task import control

logger = logging.getLogger("asynchronous_server")


def build_async_application(config: dict, *apps: str, **kwargs) -> Celery:
    """
    This function should be called within a python module called 'celery_server.py'
    Build a celery application with given configuration and modules
    :param config: Dictionary with following structure: {
        'celery': {
            'broker': ...,
            'backend': ...,
        }
    }
    :param apps: celery application modules
    :param kwargs: Additional Celery arguments
    To add celery configuration parameter, you should provide a dictionary named changes with those parameters.
    As in changes={'task_serializer': 'pickle'}
    :return: Celery Application
    """
    namespace = _namespace()
    queue = _queue()

    logger.info(f"Starting Celery server on {namespace} namespace")

    return Celery(
        "celery_server",
        broker=config["celery"]["broker"],
        # Store the state and return values of tasks
        backend=config["celery"]["backend"],
        namespace=namespace,
        include=apps,
        changes={
            "worker_hijack_root_logger": False,
            # Use pickle instead of msgpack for now as there is a bug in Celery 4.3.0 with redis
            "task_serializer": "pickle",
            "result_serializer": "pickle",
            "accept_content": ["pickle"],
            "task_compression": "gzip",
            "task_default_queue": queue,
            "task_default_exchange": queue,
            "task_default_routing_key": queue,
            **kwargs.pop("changes", {}),
        },
        **kwargs,
    )


def _get_asynchronous_task(celery_task_id: str, celery_app: Celery):
    return celery.result.AsyncResult(celery_task_id, app=celery_app)


def _result_is_available(celery_task):
    return celery_task.ready()


def _get_current_state(celery_task):
    # TODO Add more information such as request initial time, and maybe intermediate client status
    return celery_task.state


def _get_asynchronous_result(celery_app: Celery, celery_task_id: str):
    celery_task = celery.result.AsyncResult(celery_task_id, app=celery_app)
    return celery_task.get(propagate=True)


def _namespace() -> str:
    """
    Workers are started using CONTAINER_NAME environment variable as namespace or local.
    Followed by a unique identifier per machine (HOSTNAME environment variable or localhost)
    """
    return (
        f"{os.getenv('CONTAINER_NAME', 'local')}_{os.getenv('HOSTNAME', 'localhost')}"
    )


def _queue():
    """
    Workers are started using CONTAINER_NAME environment variable as queue or local.
    """
    return os.getenv("CONTAINER_NAME", "local")


def health_details():
    try:
        worker_name = f"celery@{_namespace()}"
        workers = control.ping(destination=[worker_name])
        if not workers:
            return (
                "fail",
                {
                    "celery:ping": {
                        "componentType": "component",
                        "status": "fail",
                        "time": datetime.utcnow().isoformat(),
                        "output": f"No {worker_name} workers could be found.",
                    }
                },
            )

        return (
            "pass",
            {
                "celery:ping": {
                    "componentType": "component",
                    "observedValue": workers,
                    "status": "pass",
                    "time": datetime.utcnow().isoformat(),
                }
            },
        )
    except Exception as e:
        return (
            "fail",
            {
                "celery:ping": {
                    "componentType": "component",
                    "status": "fail",
                    "time": datetime.utcnow().isoformat(),
                    "output": str(e),
                }
            },
        )
