# Changelog

## [2.0.0] - 2022-01-23
* Switch from Selenium to Playwright.
    * Fix flaky button clicks and input fills.
    * Improve performance and reliability.
    * Make it easier for users to setup.
    * Avoid ChromeDriver log messages.
    * Simplify the code and API.
* Bump required Python version to 3.9 or later.
* Update examples in `README.md` and Sphinx docs.
* Add `py.typed` to enable type checking.
* API changes:
    * `Driver` now accepts a Playwright `Browser` instead of a Selenium WebDriver.
    * `Driver` no longer accepts a `delay` argument.
    * `download_positions()` now returns a `pathlib.Path` to a temporary file.

## [1.0.3] - 2022-01-17
* Reformat changelog as Markdown.

## [1.0.2] - 2022-01-10
* Add test instructions in `README.md`.

## [1.0.1] - 2022-01-02
* Initial release.

[2.0.0]: https://github.com/qnevx/fidelipy/compare/v1.0.3...v2.0.0
[1.0.3]: https://github.com/qnevx/fidelipy/compare/v1.0.2...v1.0.3
[1.0.2]: https://github.com/qnevx/fidelipy/compare/v1.0.1...v1.0.2
[1.0.1]: https://github.com/qnevx/fidelipy/releases/tag/v1.0.1
