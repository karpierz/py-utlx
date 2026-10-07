# Copyright (c) 1994 Adam Karpierz
# SPDX-License-Identifier: Zlib

__all__ = ('has_admin_privileges',)


def has_admin_privileges() -> bool:
    """Check if the current process is running with administrator/root privileges.

    Uses UAC elevation status check.
    On XP/2003: admin == elevated (no UAC concept).

    Returns:
        True if running with admin/root privileges, False otherwise.
    """
    import sys
    from ctypes import byref, sizeof
    from . import winapi

    win_ver = sys.getwindowsversion()
    if win_ver.major < 6:  # pragma: no cover
        # Windows XP/2003 - no UAC, every admin is "elevated"
        return bool(winapi.windll.shell32.IsUserAnAdmin())

    # Vista and newer - check the token

    # Open the process token
    TOKEN_QUERY = 0x0008
    h_token = winapi.HANDLE()
    ok = winapi.OpenProcessToken(winapi.GetCurrentProcess(),
                                 TOKEN_QUERY,
                                 byref(h_token))
    if not ok:  # pragma: no cover
        return False

    # Retrieve the elevation information
    TokenElevation = 20
    elevation = winapi.DWORD()
    size      = winapi.DWORD()
    ok = winapi.GetTokenInformation(h_token, TokenElevation,
                                    byref(elevation),
                                    sizeof(elevation),
                                    byref(size))
    if not ok:  # pragma: no cover
        return False

    return bool(elevation.value)
