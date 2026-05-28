# Copyright (c) 2016 Adam Karpierz
# SPDX-License-Identifier: Zlib

from typing import TypeAlias, Any
from typing_extensions import Self
from collections.abc import Callable, Iterable, Generator
from os import PathLike
import sys
import os
import re
import stat
import shutil
import tempfile
import pathlib
import hashlib
import contextlib

import chardet

__all__ = ('Path', 'UnsupportedOperation')

StrPath:     TypeAlias = str | PathLike[str]
AnyCallable: TypeAlias = Callable[..., Any]

_HAS_FILE_ATTRS = hasattr(os.stat_result, "st_file_attributes")

if sys.version_info[:2] <= (3, 12):  # pragma: no cover
    UnsupportedOperation = NotImplementedError
else:
    from pathlib import UnsupportedOperation


class Path(pathlib.Path):

    __slots__ = ()

    if sys.version_info[:2] <= (3, 12):  # pragma: no cover
        """Constructor"""
        def __new__(cls, *args: Any, **kwargs: Any) -> Self:
            cls._flavour = (pathlib.WindowsPath  # type: ignore[union-attr]
                            if os.name == "nt" else
                            pathlib.PosixPath)._flavour
            return super().__new__(cls, *args, **kwargs)

    if sys.version_info[:2] <= (3, 11):  # pragma: no cover

        def is_relative_to(self, other: StrPath) -> bool:  # type: ignore[override]
            return super().is_relative_to(other)

        def relative_to(self, other: StrPath) -> Self:  # type: ignore[override]
            return super().relative_to(other)

    def exists(self) -> bool:
        return super().exists() or self._is_real_link()

    def mkdir(self, mode: int = 0o777,
              parents: bool = False, exist_ok: bool = True) -> None:
        return super().mkdir(mode=mode, parents=parents, exist_ok=exist_ok)

    def rmtree(self, *, ignore_errors: bool = False,
               on_error: Callable[[AnyCallable, str, Any], object] | None = None,
               onerror:  Callable[[AnyCallable, str, Any], object] | None = None) -> None:
        if not self.exists():
            return
        shutil.rmtree(self, ignore_errors=ignore_errors,
                      onerror=on_error or onerror or self.__remove_readonly)

    @staticmethod
    def __remove_readonly(func: AnyCallable, path: str, excinfo: Any) -> None:
        os.chmod(path, stat.S_IWRITE)
        func(path)

    def cleartree(self, *, ignore_errors: bool = False,
                 on_error: Callable[[AnyCallable, str, Any], object] | None = None) -> None:
        if not self.exists():
            return
        if not self.is_dir():
            raise NotADirectoryError(f"The directory name is invalid: '{self}'")
        if self._is_real_link():
            raise NotADirectoryError("Cannot call cleartree on a symbolic link")
        for entry in self.iterdir():
            if entry.is_dir() and not entry.is_symlink():
                entry.rmtree(ignore_errors=ignore_errors, on_error=on_error)
            else:
                entry.unlink(missing_ok=True)

    cleardir = cleartree  # Deprecated - only for backward compatibility

    def _is_real_link(self) -> bool:
        if _HAS_FILE_ATTRS:
            # Special handling for directory junctions to make them behave like
            # symlinks for shutil.rmtree, since in general they do not appear as
            # regular links.
            try:
                st = os.lstat(self)
                return bool(stat.S_ISLNK(st.st_mode)
                            or (st.st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT
                                and (not hasattr(os.stat_result, "st_reparse_tag")
                                     or st.st_reparse_tag == stat.IO_REPARSE_TAG_MOUNT_POINT)))
            except OSError:
                return False
        else:
            return os.path.islink(self)

    def copytree(self, target: StrPath, *, symlinks: bool = False,
                 ignore: Callable[[str, list[str]], Iterable[str]] | None = None,
                 copy_function: Callable[[str, str], object] | None = None,
                 ignore_dangling_symlinks: bool = False,
                 dirs_exist_ok: bool = False) -> Self:
        return type(self)(shutil.copytree(self, target, symlinks=symlinks, ignore=ignore,
                                          copy_function=copy_function or shutil.copy2,
                                          ignore_dangling_symlinks=ignore_dangling_symlinks,
                                          dirs_exist_ok=dirs_exist_ok))

    copydir = copytree  # Deprecated - only for backward compatibility

    def unlink(self, missing_ok: bool = True) -> None:
        try:
            return super().unlink(missing_ok=missing_ok)
        except PermissionError:
            self.chmod(stat.S_IWRITE)
            return super().unlink(missing_ok=missing_ok)

    if sys.version_info[:2] <= (3, 13):

        def copy(self, target: StrPath, *,
                 follow_symlinks: bool = True, preserve_metadata: bool = False) -> Self:
            """Recursively copy this file or directory tree to the given destination."""
            if not hasattr(target, "with_segments"):
                target = self.with_segments(target)
            assert isinstance(target, type(self))
            if self.is_dir():
                if not follow_symlinks and self.is_symlink():
                    self._copy_symlink(target, preserve_metadata)
                else:
                    self.copytree(target,
                                  symlinks=not follow_symlinks,
                                  ignore_dangling_symlinks=False,
                                  dirs_exist_ok=False)
            else:
                type(self)(shutil.copy2(self, target, follow_symlinks=follow_symlinks))
            # No action needed for preserve_metadata. copytree and copy2 always copies metadata
            # if preserve_metadata or os.name == "nt":
            #     shutil.copystat(self, copied, follow_symlinks=follow_symlinks)
            return target.joinpath()  # Empty join to ensure fresh metadata.

        def _copy_symlink(self, target: StrPath, preserve_metadata: bool = False) -> None:
            # If a directory-symlink is copied *before* its target, then
            # os.symlink() incorrectly creates a file-symlink on Windows. Avoid
            # this by passing *target_is_dir* to os.symlink() on Windows.
            os.symlink(self.readlink(), target, self.is_dir())
            # if preserve_metadata:
            #     _copy_info(self.info, target, follow_symlinks=False)

        def copy_into(self, target_dir: StrPath, *,
                      follow_symlinks: bool = True, preserve_metadata: bool = False) -> Self:
            """Copy this file or directory tree into the given existing directory."""
            name = self.name
            if not name:
                raise ValueError(f"{self!r} has an empty name")
            elif hasattr(target_dir, "with_segments"):
                target = target_dir / name  # type: ignore[operator]
            else:
                target = self.with_segments(target_dir, name)
            if not target.parent.exists():
                raise FileNotFoundError("The system cannot find the path specified: "
                                        f"'{target_dir}'")
            return self.copy(target,
                             follow_symlinks=follow_symlinks,
                             preserve_metadata=preserve_metadata)

        def move(self, target: StrPath) -> Self:
            return type(self)(shutil.move(self, target, copy_function=shutil.copy2))

        def move_into(self, target_dir: StrPath) -> Self:
            """Move this file or directory tree into the given existing directory."""
            name = self.name
            if not name:
                raise ValueError(f"{self!r} has an empty name")
            elif hasattr(target_dir, "with_segments"):
                target = target_dir / name  # type: ignore[operator]
            else:
                target = self.with_segments(target_dir, name)
            return self.move(target)

        if sys.version_info[:2] <= (3, 11):  # pragma: no cover

            def with_segments(self, *pathsegments: Any) -> Self:
                """Construct a new path object from any number of path-like objects.

                Subclasses may override this method to customize how new path objects
                are created from methods like `iterdir()`.
                """
                return type(self)(*pathsegments)

    else: pass  # pragma: no cover

    def copystat(self, target: StrPath, *, follow_symlinks: bool = True) -> None:
        return shutil.copystat(self, target, follow_symlinks=follow_symlinks)

    @classmethod
    def which(cls, cmd: StrPath, *, mode: int = os.F_OK | os.X_OK,
              path: StrPath | None = None) -> Self | None:
        result = shutil.which(str(cmd), mode=mode, path=path)
        return cls(result) if result is not None else None

    def file_hash(self, algorithm: str, *, chuck_size: int = 65536) -> Any:
        constructor = self.__hash_algorithms.get(algorithm, lambda: hashlib.new(algorithm))
        hash_value = constructor()
        with self.open("rb") as f:
            while True:
                chunk = f.read(chuck_size)
                if not chunk: break
                hash_value.update(chunk)
        return hash_value

    def dir_hash(self, algorithm: str, *, chuck_size: int = 65536) -> Any:
        constructor = self.__hash_algorithms.get(algorithm, lambda: hashlib.new(algorithm))
        hash_value = constructor()
        for root, dirs, files in os.walk(self):
            for name in files:
                fpath = Path(root)/name
                with fpath.open("rb") as f:
                    while True:
                        chunk = f.read(chuck_size)
                        if not chunk: break
                        hash_value.update(chunk)
        return hash_value

    __hash_algorithms: dict[str, Callable[[], Any]] = {
        "md5":     hashlib.md5,
        "sha1":    hashlib.sha1,
        "sha224":  hashlib.sha224,
        "sha256":  hashlib.sha256,
        "sha384":  hashlib.sha384,
        "sha512":  hashlib.sha512,
        "blake2b": hashlib.blake2b,
        "blake2s": hashlib.blake2s,
    }

    def unpack_archive(self, extract_dir: StrPath | None = None, *,
                       format: str | None = None) -> None:  # noqa: A002
        """Unpack an archive."""
        return shutil.unpack_archive(self, extract_dir, format)

    def sed_inplace(self, pattern: str | re.Pattern[str], repl: str, *,
                    flags: int | re.RegexFlag = 0, encoding: str | None = None) -> None:
        """Perform the pure-Python equivalent of in-place `sed` substitution: e.g., \
        `sed -i -e 's/'${pattern}'/'${repl}'/g "${filename}"`."""

        # For efficiency, precompile the passed regular expression.
        if not isinstance(pattern, re.Pattern): pattern = re.compile(pattern, flags)

        if encoding is not None:
            content = self.open("rt", encoding=encoding, newline="").read()
        else:
            data = self.read_bytes()
            detected = chardet.detect(data, prefer_superset=False, compat_names=False)
            encoding = detected["encoding"]
            try:
                content = data.decode(encoding) if encoding else data.decode()
            except Exception:
                raise UnicodeError(f"The file '{self}' cannot be decoded. "
                                   f"It appears to be a binary file.")

        with tempfile.NamedTemporaryFile(mode="wt", encoding=encoding,
                                         newline="", delete=False) as tmp_file:
            if flags & re.MULTILINE:
                tmp_file.write(pattern.sub(repl, content))
            else:
                for line in content.splitlines(keepends=True):
                    tmp_file.write(pattern.sub(repl, line))
        # Overwrite the original file with the munged temporary file
        # in a manner preserving file attributes (e.g., permissions).
        shutil.copystat(self, tmp_file.name)
        shutil.move(tmp_file.name, self)

    def chdir(self) -> None:
        os.chdir(self)

    @contextlib.contextmanager
    def pushd(self) -> Generator[None, None, None]:
        curr_dir = os.getcwd()
        os.chdir(self)
        try:
            yield
        finally:
            os.chdir(curr_dir)


del Self, Callable, Iterable, Generator, PathLike
del StrPath, AnyCallable
