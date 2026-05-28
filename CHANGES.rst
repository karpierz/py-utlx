Changelog
=========

2.3.1 (2026-03-31)
------------------
- Added support for Python 3.15
- | Improved compatibility with pathlib (especially for Python >= 3.14).
  | POTENTIAL BACKWARD INCOMPATIBILITIES:

  - | Renamed the incompatible patched utlx.epath.rmdir() to rmtree() (still
    | provided as an extension to the original pathlib).
  - | The old 'onexc' parameter of utlx.epath.rmdir() has been renamed to
    | 'on_error' in rmtree (or 'onerro'r for compatibility with pathlib3x).
  - | The 'onexc' parameter of utlx.epath.cleardir() has been renamed to
    | 'on_error'.
  - | The 'copy_function' parameter has been removed from utlx.epath.move()
    | for compatibility with the original pathlib.
  - | utlx.epath.move() now raises FileNotFoundError when the source (self)
    | does not exist - changed for compatibility with the original pathlib.

- | Renamed copydir() to copytree().
  | The old name is kept as a deprecated alias for backward compatibility.
- | Renamed cleardir() to cleartree().
  | The old name is kept as a deprecated alias for backward compatibility.
- | utlx.epath.move() is now pathlib.move() for Python >= 3.14 instead of
  | being a wrapper around shutil.move().
- | utlx.epath.copy() is now pathlib.copy() for Python >= 3.14 instead of
  | being a wrapper around shutil.copy2(). Also, the utlx.epath.copy()
  | wrapper is now much more compatible with pathlib.copy().
  | It now allows copying directories and symbolic links as well.
- Added the 'preserve_metadata' parameter to utlx.epath.copy().
- Added a pathlib-compatible utlx.epath.copy_into().
- Added a pathlib-compatible utlx.epath.move_into().
- Added a pathlib-compatible utlx.epath.with_segments() for Python <= 3.11
- Added a pathlib-compatible utlx.epath.UnsupportedOperation exception.
- | Added __slots__ to utlx.epath.Path to reduce memory usage and prevent
- | dynamic attributes, matching pathlib.Path behavior.
- Switched from charset_normalizer to chardet.
- Setup updates and improvements.

2.1.2 (2026-01-30)
------------------
- utlx.epath.Path.copydir() - added dirs_exist_ok parameter.
- utlx.platform.*.capi  - added in_addr_t.
- utlx.platform.windows - added winapi.
- utlx.platform.macos   - added macos_version().
- utlx.platform.windows.winapi - added OpenProcessToken(),
  GetTokenInformation().
- run(): cleanup and improvements.
- Much better typing.
- Some minor cleanup and unifications.
- Version number alignment (-> 2.x.x).
- Copyright year update.
- Switched from tox to Nox for project automation.
- The documentation has been moved from Read the Docs to GitHub Pages.
- Added the nox's 'cleanup' test environment.
- Setup update (mainly dependencies) and bug fixes.

1.0.0 (2025-09-09)
------------------
- Making and mark the package typed.
- 100% code linting.
- 100% code coverage.
- Setup update (mainly dependencies).

0.1.0 (2025-09-01)
------------------
- First public release.

0.0.0 (2025-07-17)
------------------
- Initial commit.
