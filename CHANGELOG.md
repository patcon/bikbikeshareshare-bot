# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]
### Fixed
- Fix that open trips were't shown when fetching last ride.
- Fix Signal messages enable to be sent to dbus on Ubuntu.

### Added
- Swagger spec for Bikeshare API.
- Command to check trip status with :stopwatch: #16
- Command to search for nearest station. #2

## [0.2.0] - 2021-04-29
### Added
- Echo ride duration after checkin messages, for both open
  :hourglass_flowing_sand: and closed :hourglass: rides.
    > `you` :lock::arrow_left::bike:  
    > `bot` :hourglass: :one::zero: :four::three:

## [0.1.0] - 2021-04-26
### Added
- Initial code release: Send ride code in reply to "bike please" :bike::pray: location message.

## 0.0.1
### Added
- No-code, purely social protocol in Signal group.

<!-- Links -->
   [Unreleased]: https://github.com/patcon/bikebikeshareshare-bot/compare/v0.2.0...HEAD
   [0.2.0]: https://github.com/patcon/bikebikeshareshare-bot/compare/v0.1.0...v0.2.0
   [0.1.0]: https://github.com/patcon/bikebikeshareshare-bot/releases/tag/v0.1.0
