# Copyright (c) 2018 Adam Karpierz
# SPDX-License-Identifier: Zlib

import ctypes
from pathlib import Path

__all__ = ('dll_path', 'python_dll_path')


def dll_path(handle: ctypes.CDLL | int) -> Path | None:
    """Retrieves the fully qualified path for the file that contains the specified module.

    The module must have been loaded by the current process.
    """
    import ctypes
    from ctypes.wintypes import HMODULE, LPWSTR, DWORD
    MAX_PATH = 520
    if isinstance(handle, ctypes.CDLL): handle = int(handle._handle)
    GetModuleFileNameW = ctypes.windll.kernel32.GetModuleFileNameW
    GetModuleFileNameW.restype  = DWORD
    GetModuleFileNameW.argtypes = [HMODULE, LPWSTR, DWORD]
    buf = ctypes.create_unicode_buffer(MAX_PATH)
    result = GetModuleFileNameW(handle, buf, len(buf))
    dll_path = buf.value
    # print("@@@@@@@@@@@", handle, result, dll_path)
    return (Path(dll_path) if handle != 0 and result != 0
            and dll_path and Path(dll_path).exists() else None)


def python_dll_path() -> Path | None:
    """Retrieves the fully qualified path for the file that contains Python dll module.

    The module must have been loaded by the current process.
    """
    try:
        from ctypes import pythonapi
    except ImportError:  # pragma: no cover
        from sys import dllhandle
    else:
        dllhandle = pythonapi._handle
    return dll_path(dllhandle)
