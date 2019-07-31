from collections import namedtuple

import pytest

from flasynk import celery_specifics


@pytest.fixture
def reset_current_task():
    yield 1
    celery_specifics.current_task = None


def test_celery_is_none():
    req_filter = celery_specifics.CeleryTaskIdFilter()
    dummy_record = namedtuple("Record", "request_id")
    req_filter.filter(dummy_record)
    assert "" == dummy_record.request_id


def test_celery_is_not_none_but_request_is_none(reset_current_task):
    celery_specifics.current_task = namedtuple("DummyCelery", "request")
    req_filter = celery_specifics.CeleryTaskIdFilter()
    dummy_record = namedtuple("Record", "request_id")
    req_filter.filter(dummy_record)
    assert "" == dummy_record.request_id


def test_request_not_none_but_id_is_none(reset_current_task):
    celery_specifics.current_task = namedtuple("DummyCelery", "request")
    celery_specifics.current_task.request = namedtuple("DummyCeleryRequest", "aa")
    req_filter = celery_specifics.CeleryTaskIdFilter()
    dummy_record = namedtuple("Record", "request_id")
    req_filter.filter(dummy_record)
    assert "" == dummy_record.request_id


def test_request_none_is_none(reset_current_task):
    celery_specifics.current_task = namedtuple("DummyCelery", "request")
    celery_specifics.current_task.request = namedtuple("DummyCeleryRequest", "id")
    celery_specifics.current_task.request.id = "bite my shiny metal ass"
    req_filter = celery_specifics.CeleryTaskIdFilter()
    dummy_record = namedtuple("Record", "request_id")
    req_filter.filter(dummy_record)
    assert "bite my shiny metal ass" == dummy_record.request_id
