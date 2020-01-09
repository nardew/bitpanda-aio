# Changelog

All notable changes to this project will be documented in this file.

The project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Pending release]

## [1.0.0] - 2020-01-09

### Added

- Market, limit and stop limit orders support `client_id` property
- Limit and stop limit orders support `time_in_force` property
- REST calls print how much time was spent waiting for a reply (visible only in debug mode)

### Changed

- __Important!!!__ REST response body is not returned as a string anymore but as a dictionary instead. If you did `json.loads(response['response'])` before, now use only `response['response']`.

[Pending release]: https://github.com/nardew/bitpanda-aio/compare/1.0.0...HEAD
[1.0.0]: https://github.com/nardew/bitpanda-aio/compare/0.1.0...1.0.0