# Change Log
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/)
and this project adheres to [Semantic Versioning](http://semver.org/).

## [2.6.0] - 2022/11/17
- [DCAEGEN2-2953] Code refactoring

## [2.5.0] - 2022/10/25
- [DCAEGEN2-2952] Handle exception when MR is unavailable
- [DCAEGEN2-3297] Fix Black tool compatibility issue blocking docker build

## [2.4.1] - 2022/09/23
- [DCAEGEN2-2837] Heartbeat ms: remove unnecessary parenthesis, use lowercase variable name
- [DCAEGEN2-3268] Fix cryptography version to 37.0.4

## [2.4.0] - 2021/10/12
### Changed
- [DCAEGEN2-2939] Removed unused code (config\_notif.py)
- [DCAEGEN2-2995] run the black formatting tool on python code
### Fixed
- [DCAEGEN2-2832] Pod become unready state
- [DCAEGEN2-2872] No such file or directory error and stop working
- [DCAEGEN2-2940] Microsec timestamp not properly handled
- [DCAEGEN2-2941] Log file fragmented by log rotation
- [DCAEGEN2-2944] cbs polling process startup failure


## [2.3.1.] - 2021/06/19
### Security
- Fixed SQL injection vulnerability
### Changed
- Cleanup code
  - Removed extraneous parentheses
- Use yyyy/mm/dd format in Changelog
- Removed volume mapping from Dockerfile
- Switched to CBS client 2.2.1
### Fixed
- pytest fails if http\_proxy is set


## [2.3.0.] - 2021/06/18
### Changed
- Cleanup code
  - Removed unused imports
  - Removed unused code
  - Reformatted code whitespace
- Add target/ to .gitignore


## [2.2.0.] - 2021/04/07
### Changed
- Switched to currently recommended version of docker integration-python:8.0.0.
- Fix issues preventing running with py3.9
- Bumped tested python versions to 3.8,3.9.
### Security
- Due to dependency update following were fixed:
  - CVE-2020-14343 (PyYAML)
  - CWE-93 (httplib2)
  - CVE-2018-18074 (requests)

## [2.1.1.] - 2021/02/03
