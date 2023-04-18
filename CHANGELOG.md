<a name="0.3.4"></a>
## [0.3.4] - 2023-03-23

### Documentation
- add info to important settings
- update run-local instructions

### Maintenance
- use a minimalistic deploy bash script and change GitHub actions CI
- write a simple bash script for backing up the [SQLite3] database
- add `systemd` config for [gunicorn] service, making start-up faster and more seamless
- switch from [Apache 2] and [`mod_wsgi`] to [gunicorn] & [nginx]
- get config from environment variables (fixes [#97])
- send all logs only to stdout (fixes [#96])
- move config into `pyproject.toml`, making dependency installation more effortless (relates to [#95])

[SQLite3]: https://www.sqlite.org/index.html
[Apache 2]: https://httpd.apache.org/
[`mod_wsgi`]: https://modwsgi.readthedocs.io/en/master/
[gunicorn]: https://gunicorn.org/
[nginx]: https://nginx.org/en/


<a name="0.3.3"></a>
## [0.3.3] - 2023-03-08

### Bug Fixes
- revert syntax to python 3.8


<a name="0.3.2"></a>
## [0.3.2] - 2023-03-08

### Bug Fixes
- new query produces fewer SQL lines, thereby fixing [#89]
- patient list working again after new query broke it

### Documentation
- switch to markdown for `README.md`
- improve `README.md`
- correct two small errors in static texts
- improve query function's docstrings

### Testing
- Implement some unit tests for new querying


<a name="0.3.1"></a>
## [0.3.1] - 2023-03-06

### Code Refactoring
- make `DashboardView` methods more reusable
- modularize dashboard HTML layout
- put dashboard help templates in separate folder

### Features
- dashboard uses AJAX now (fixes [#94])

### Maintenance
- use conventional commits & start changelog

## Before [0.3.0] - 2023-03-02

Commits before the 2nd of March 2023 did not use conventional commits and no changelog was maintained. For completeness, we give the links to the respective diffs of previous releases below.

- [0.3.0] - 2022-07-05
- [0.2.17] - 2022-06-02
- [0.2.16] - 2022-05-24
- [0.2.15] - 2022-04-08
- [0.2.14] - 2022-02-01
- [0.2.13] - 2022-01-27
- [0.2.12] - 2022-01-14
- [0.2.11] - 2022-01-13
- [0.2.10] - 2021-12-07
- [0.2.9] - 2021-11-03
- [0.2.8] - 2021-10-29
- [0.2.7] - 2021-10-28
- [0.2.6] - 2021-10-20
- [0.2.5] - 2021-10-19
- [0.2.4] - 2021-10-06
- [0.2.3] - 2021-10-04
- [0.2.2] - 2021-10-04
- [0.2.1] - 2021-10-04
- [0.2.0] - 2021-10-04
- [0.1.4] - 2021-10-04
- [0.1.3] - 2021-10-04
- [0.1.2] - 2021-10-04
- [0.1.1] - 2021-10-04
- [0.1.0] - 2021-10-04
- [0.0.2] - 2021-10-04
- 0.0.1 - 2021-10-04

[Unreleased]: https://github.com/rmnldwg/lyprox/compare/0.3.4...HEAD
[0.3.4]: https://github.com/rmnldwg/lyprox/compare/0.3.3...0.3.4
[0.3.3]: https://github.com/rmnldwg/lyprox/compare/0.3.2...0.3.3
[0.3.2]: https://github.com/rmnldwg/lyprox/compare/0.3.1...0.3.2
[0.3.1]: https://github.com/rmnldwg/lyprox/compare/0.3.0...0.3.1
[0.3.0]: https://github.com/rmnldwg/lyprox/compare/0.2.17...0.3.0
[0.2.17]: https://github.com/rmnldwg/lyprox/compare/0.2.16...0.2.17
[0.2.16]: https://github.com/rmnldwg/lyprox/compare/0.2.15...0.2.16
[0.2.15]: https://github.com/rmnldwg/lyprox/compare/0.2.14...0.2.15
[0.2.14]: https://github.com/rmnldwg/lyprox/compare/0.2.13...0.2.14
[0.2.13]: https://github.com/rmnldwg/lyprox/compare/0.2.12...0.2.13
[0.2.12]: https://github.com/rmnldwg/lyprox/compare/0.2.11...0.2.12
[0.2.11]: https://github.com/rmnldwg/lyprox/compare/0.2.10...0.2.11
[0.2.10]: https://github.com/rmnldwg/lyprox/compare/0.2.9...0.2.10
[0.2.9]: https://github.com/rmnldwg/lyprox/compare/0.2.8...0.2.9
[0.2.8]: https://github.com/rmnldwg/lyprox/compare/0.2.7...0.2.8
[0.2.7]: https://github.com/rmnldwg/lyprox/compare/0.2.6...0.2.7
[0.2.6]: https://github.com/rmnldwg/lyprox/compare/0.2.5...0.2.6
[0.2.5]: https://github.com/rmnldwg/lyprox/compare/0.2.4...0.2.5
[0.2.4]: https://github.com/rmnldwg/lyprox/compare/0.2.3...0.2.4
[0.2.3]: https://github.com/rmnldwg/lyprox/compare/0.2.2...0.2.3
[0.2.2]: https://github.com/rmnldwg/lyprox/compare/0.2.1...0.2.2
[0.2.1]: https://github.com/rmnldwg/lyprox/compare/0.2.0...0.2.1
[0.2.0]: https://github.com/rmnldwg/lyprox/compare/0.1.4...0.2.0
[0.1.4]: https://github.com/rmnldwg/lyprox/compare/0.1.3...0.1.4
[0.1.3]: https://github.com/rmnldwg/lyprox/compare/0.1.2...0.1.3
[0.1.2]: https://github.com/rmnldwg/lyprox/compare/0.1.1...0.1.2
[0.1.1]: https://github.com/rmnldwg/lyprox/compare/0.1.0...0.1.1
[0.1.0]: https://github.com/rmnldwg/lyprox/compare/0.0.2...0.1.0
[0.0.2]: https://github.com/rmnldwg/lyprox/compare/0.0.1...0.0.2

[#89]: https://github.com/rmnldwg/lyprox/issues/89
[#94]: https://github.com/rmnldwg/lyprox/issues/94
[#95]: https://github.com/rmnldwg/lyprox/issues/95
[#96]: https://github.com/rmnldwg/lyprox/issues/96
[#97]: https://github.com/rmnldwg/lyprox/issues/97
