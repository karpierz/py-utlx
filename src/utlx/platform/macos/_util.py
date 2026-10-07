# Copyright (c) 1994 Adam Karpierz
# SPDX-License-Identifier: Zlib

__all__ = ('has_admin_privileges',)


def has_admin_privileges() -> bool:
    """Check if the current process is running with administrator/root privileges.

    Checks if running as root (UID == 0).

    Returns:
        True if running with admin/root privileges, False otherwise.
    """
    import os
    return os.getuid() == 0 if hasattr(os, "getuid") else False
