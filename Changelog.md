# Change Log
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/)
and this project adheres to [Semantic Versioning](http://semver.org/).

## [Unreleased]
### Changed
- Cleanup code
  - Removed unused imports

## [2.2.0.] - 07/04/2021
### Changed
- Switched to currently recommended version of docker integration-python:8.0.0.
- Fix issues preventing running with py3.9
- Bumped tested python versions to 3.8,3.9.
### Security
- Due to dependency update following were fixed:
  - CVE-2020-14343 (PyYAML)
  - CWE-93 (httplib2)
  - CVE-2018-18074 (requests)

## [2.1.1.] - 03/02/2021
