# Change Log
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/)
and this project adheres to [Semantic Versioning](http://semver.org/).

## [2.4.0.] - 2021/10/12
### Changed
- Removed unused code (config_notif.py)

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
