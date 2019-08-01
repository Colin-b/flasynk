<h2 align="center">Exposing Asynchronous endpoint using Flask-RestPlus</h2>

<p align="center">
<a href="https://github.com/psf/black"><img alt="Code style: black" src="https://img.shields.io/badge/code%20style-black-000000.svg"></a>
<a href='https://pse.tools.digital.engie.com/drm-all.gem/job/team/view/Python%20modules/job/flasynk/job/master/'><img src='https://pse.tools.digital.engie.com/drm-all.gem/buildStatus/icon?job=team/flasynk/master'></a>
<a href='https://pse.tools.digital.engie.com/drm-all.gem/job/team/view/Python%20modules/job/flasynk/job/master/cobertura/'><img src='https://pse.tools.digital.engie.com/drm-all.gem/buildStatus/icon?job=team/flasynk/master&config=testCoverage'></a>
<a href='https://pse.tools.digital.engie.com/drm-all.gem/job/team/view/Python%20modules/job/flasynk/job/master/lastSuccessfulBuild/testReport/'><img src='https://pse.tools.digital.engie.com/drm-all.gem/buildStatus/icon?job=team/flasynk/master&config=testCount'></a>
</p>

## Mocking Celery with pytest

```python
from flasynk.celery_mock import *

@pytest.fixture
def celery_app_func():
    return the_function_returning_the_celery_app


def test_something(mock_celery):
    pass
```

## Mocking Huey with pytest

```python
from flasynk.huey_mock import *

@pytest.fixture
def huey_app_func():
    return the_function_returning_the_huey_app


def test_something(mock_huey):
    pass
```

## How to install
1. [python 3.7+](https://www.python.org/downloads/) must be installed
2. Use pip to install module:
```sh
python -m pip install flasynk -i https://all-team-remote:tBa%40W%29tvB%5E%3C%3B2Jm3@artifactory.tools.digital.engie.com/artifactory/api/pypi/all-team-pypi-prod/simple
```
