import logging
import os

from huey import RedisHuey
from huey.exceptions import TaskException


logger = logging.getLogger("asynchronous_server")

# List all statements that should be executed before evaluating an Exception that occurred.
imported_exceptions = []


def build_async_application(config: dict, **kwargs) -> RedisHuey:
    """
    This function should be called within a python module called 'asynchronous_server.py'
    Build a huey application with given configuration and modules
    :param config: Dictionary with following structure: {
        'asynchronous': {
            'broker': ...,
        }
    }
    :param kwargs: Additional Huey arguments
    :return: RedisHuey Application
    """
    logger.info(f"Starting Huey server")
    return RedisHuey(
        os.getenv("CONTAINER_NAME", "LOCAL"),
        url=config["asynchronous"]["broker"],
        **kwargs,
    )


def _get_asynchronous_task(huey_task_id: str, huey_app: RedisHuey):
    try:
        return huey_app.result(huey_task_id, preserve=True)
    except:
        return "Exception"


def _result_is_available(huey_task):
    return huey_task is not None


def _get_current_state(huey_task):
    # TODO Add more information such as request initial time, and maybe intermediate client status
    return "PENDING"


def _get_asynchronous_result(huey_app: RedisHuey, huey_task_id: str):
    try:
        huey_task = huey_app.result(huey_task_id)
    except TaskException as e:
        try:
            for import_exception in imported_exceptions:
                exec(import_exception)
            task_exception = eval(e.metadata["error"])
        except NameError:
            task_exception = Exception(e.metadata["error"])
        raise task_exception
    return huey_task
