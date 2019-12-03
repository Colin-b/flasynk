<h2 align="center">Exposing Asynchronous endpoint using Flask-RestPlus</h2>

<p align="center">
<a href="https://pypi.org/project/flasynk/"><img alt="pypi version" src="https://img.shields.io/pypi/v/flasynk"></a>
<a href="https://travis-ci.org/Colin-b/flasynk"><img alt="Build status" src="https://api.travis-ci.org/Colin-b/flasynk.svg?branch=develop"></a>
<a href="https://travis-ci.org/Colin-b/flasynk"><img alt="Coverage" src="https://img.shields.io/badge/coverage-100%25-brightgreen"></a>
<a href="https://github.com/psf/black"><img alt="Code style: black" src="https://img.shields.io/badge/code%20style-black-000000.svg"></a>
<a href="https://travis-ci.org/Colin-b/flasynk"><img alt="Number of tests" src="https://img.shields.io/badge/tests-34 passed-blue"></a>
<a href="https://pypi.org/project/flasynk/"><img alt="Number of downloads" src="https://img.shields.io/pypi/dm/flasynk"></a>
</p>

## Mocking Celery

To mock celery, the best is still to use the celery_mock.CeleryMock class.

## Mocking Huey

To mock huey, the best is still to update the Huey application before starting the Flask app by setting immediate to True.

## How to install
1. [python 3.7+](https://www.python.org/downloads/) must be installed
2. Use pip to install module:
```sh
python -m pip install flasynk
```
