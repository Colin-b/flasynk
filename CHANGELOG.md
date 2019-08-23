# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.3.0] - 2019-08-23
### Changed
- Update flask-restplus to version 0.13.0
- Update huey to version 2.1.1
- Update redis to version 3.3.8
- Remove pre-commit from dependencies and explain how to install the python module to contribute

## [1.2.0] - 2019-08-01
### Changed
- Update redis to version 3.3.4
- Add celery_specifics.CeleryTaskIdFilter

### Added
- Fixture to mock celery
- Fixture to mock huey

## [1.1.0] - 2019-07-30
### Changed
- Update pre-commit to version 1.17.0
- Update huey to version 2.1.0
- Update redis to version 3.3.0
- Use pytest-flask instead of Flask-Testing
- Use pytest instead of unittest

## [1.0.2] - 2019-05-14
### Fixed
- [Huey] Redis dependency was missing.

## [1.0.1] - 2019-05-10
### Changed
- [Celery] Hide more mock methods.

## [1.0.0] - 2019-05-10
### Added
- Initial release.

[Unreleased]: https://github.tools.digital.engie.com/GEM-Py/flasynk/compare/v1.3.0...HEAD
[1.3.0]: https://github.tools.digital.engie.com/GEM-Py/flasynk/compare/v1.2.0...v1.3.0
[1.2.0]: https://github.tools.digital.engie.com/GEM-Py/flasynk/compare/v1.1.0...v1.2.0
[1.1.0]: https://github.tools.digital.engie.com/GEM-Py/flasynk/compare/v1.0.2...v1.1.0
[1.0.2]: https://github.tools.digital.engie.com/GEM-Py/flasynk/compare/v1.0.1...v1.0.2
[1.0.1]: https://github.tools.digital.engie.com/GEM-Py/flasynk/compare/v1.0.0...v1.0.1
[1.0.0]: https://github.tools.digital.engie.com/GEM-Py/flasynk/releases/tag/v1.0.0
