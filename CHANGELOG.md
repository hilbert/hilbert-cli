# Change Log

## [Unreleased]

### Changed
### Added
### Security

## [0.9.0] - 2017-05-06

### Changed
- Fixed issues due to global system installation 

### Added
- Helpers due to global system installation 
- Sample NODM configuration + .xsession
- Sample station configurations (minimal + testapp)
- Initial RPM .spec files for a station

## [0.8.0] - 2017-02-13

### Added
- [Semantic Versioning](http://semver.org/)
- Changelog according to (http://keepachangelog.com/)
- License: Apache v2
- Git branching model
- Server-side Hilbert CLI (python) tool: `tools/hilbert` (low-level management using Hilbert YAML Configuration)
- Client-side Hilbert CLI (bash) tool: `tools/hilbert-station` (low-level wrapper around docker/docker-compose and run remote actions for the server-side tool)

### Changed
- Restructurization/migration of older `malex984/dockapp` into sparate repos: `hilbert/hilbert-cli`, `hilbert/hilbert-heartbeat`, `hilbert/hilbert-docker-images`
- Migration of high-level scripts from Dashboard to `hilbert/hilbert-cli`

### Security 
- Starting to remove `sudo` and `privileged` requirements (and pid=host)

## [0.1.0] - 2016-09-02
### Added
- Basic back-end management scripts for server and staions
- Integration of management scripts with the Dashboard's back-end server within `:mng`
- First working system prototype using manual configurations


### Changed
- Switch of run-time from docker to docker-compose
- Station images can be pulled from a private registry

## 0.0.1 - 2015-08-13
### Added
- Run-time using docker
- Proof-of-concept demo scripts and driver images (`:main` and later `:demo`) 


[Unreleased]: https://github.com/hilbert/hilbert-cli/compare/v0.9.0...HEAD
[0.9.0]: https://github.com/hilbert/hilbert-cli/compare/v0.8.0...v0.9.0
[0.8.0]: https://github.com/hilbert/hilbert-cli/compare/v0.8.0...v0.1.0
[0.1.0]: https://github.com/hilbert/hilbert-cli/compare/v0.0.1...v0.1.0
