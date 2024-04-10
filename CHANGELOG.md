# Changelog

All notable changes to this project will be documented in this file.

<a name="0.4.3"></a>
## [0.4.3] - 2024-04-10

### 🐛 Bug Fixes

- Update initial datasets JSON file
- Don't allow nginx access to any files in the server dir. Fixes [#115].

### Build

- Bump git-cliff


<a name=0.4.1></a>
## [0.4.2] - 2024-03-15

### Change

- Update initial riskmodels

### Ci

- Bump python version for building docs
- Fix python version in docs build

### Feat

- Add UMCG institution & prelim dataset
- Add UMCG surgical dataset to initial
- Add hans langendijk to initial users

### Fix

- Refs parsed as equation
- Throw better error when GitHub token expired


<a name=0.4.1></a>
## [0.4.1] - 2023-12-05

### Bug Fixes

- Don't use `format()` on markdown string containing LaTeX (fixes [#111])

### Features

- Render LaTeX equations in README of risk models

### Miscellaneous Tasks

- Deployment script (GitHub actions) runs more stably now and accepts inputs (fixes [#110])


<a name="0.4.0"></a>
## [0.4.0] - 2023-11-28

### Bug Fixes
- add minor version to all dependencies
- store GitHub/repo related `Dataset` info in fields to reduce number of API calls
- `Dataset` import now works with private repos and stores them hidden behind authentication
- set initial diagnosis in risk predictor to be all negative (cN0), fixes [#104]
- replace `core` with `lyprox` in some places
- simplify permissions in setup.sh
- add `BASE_DIR` to settings fetched from env vars, to avoid it being inside site-packages
- `get` templatetag catches KeyErrors
- make midline in risk predictor subset of bilateral
- fix JS not updating data explorer values of 0
- risk predictor sensitivity & specificity start at 50%
- risk predictor form shows error when midline is not set
- make AJAX update data-tooltips, fixes [#99]

### Code Refactoring
- trim down duplicate & unused CSS code, related to [#100]
- pull apart CSS files in dataexplorer, related to [#100]
- clean up index templates & static files, related to [#100]
- put publication data in YAML file, related to [#100]
- use sekizai to make index modular, related to [#100]
- modularize navbar, related to [#100]
- move tags from `patients` app to `lyprox` root
- manage.py script & custom bulma sass
- move apps into lyprox directory
- rename `core` to `lyprox`

### Documentation
- update home, add link to lynference revision
- add help tooltips to risk predictor

### Features
- add T0 button to the Data Explorer. Fixes [#108]
- add commands `add_institutions`, `add_users`, `add_datasets`, and `add_riskmodels` twith which one can either initialize the respective models from a JSON file or add individual instances using command line arguments. This fixes [#109]
- enable dataset to detect corruption via SHA value of file
- allow datasets to be uploaded via GitHub, fixes [#103]
- add download button & link to dataset readme
- add ability to login-protect entire site
- add errorbars to risk predictor app
- add selected model params to risk predictor app
- add description & params to risk predictor dashboard
- add inference result description to list
- add spinner to model upload button
- implement AJAX request for risk prediction
- sync position & value of sens/spec slider
- add list view of precomputed, trained models
- add lymph model & form to get it from repository (e.g. [lynference])
- implement risk predictor, fixes [#15]

### Maintenance
- replace migration with command for initial user and institution data
- add Esmee to initial user database

### Testing
- write tests for dataset functionality


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


[lynference]: https://github.com/rmnldwg/lynference

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

[Unreleased]: https://github.com/rmnldwg/lyprox/compare/0.4.3...HEAD
[0.4.3]: https://github.com/rmnldwg/lyprox/compare/0.4.2...0.4.3
[0.4.2]: https://github.com/rmnldwg/lyprox/compare/0.4.1...0.4.2
[0.4.1]: https://github.com/rmnldwg/lyprox/compare/0.4.0...0.4.1
[0.4.0]: https://github.com/rmnldwg/lyprox/compare/0.3.4...0.4.0
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

[#15]: https://github.com/rmnldwg/lyprox/issues/15
[#89]: https://github.com/rmnldwg/lyprox/issues/89
[#94]: https://github.com/rmnldwg/lyprox/issues/94
[#95]: https://github.com/rmnldwg/lyprox/issues/95
[#96]: https://github.com/rmnldwg/lyprox/issues/96
[#97]: https://github.com/rmnldwg/lyprox/issues/97
[#99]: https://github.com/rmnldwg/lyprox/issues/99
[#100]: https://github.com/rmnldwg/lyprox/issues/100
[#103]: https://github.com/rmnldwg/lyprox/issues/103
[#104]: https://github.com/rmnldwg/lyprox/issues/104
[#108]: https://github.com/rmnldwg/lyprox/issues/108
[#109]: https://github.com/rmnldwg/lyprox/issues/109
[#110]: https://github.com/rmnldwg/lyprox/issues/110
[#111]: https://github.com/rmnldwg/lyprox/issues/111
[#115]: https://github.com/rmnldwg/lyprox/issues/115
