# flake8-in-file-ignores: noqa: A005,F401,F403,F405

# Copyright (c) 1994 Adam Karpierz
# SPDX-License-Identifier: Zlib

from ._detect import *
from ._oid    import *
if is_windows:  # pragma: no cover
    from .windows import arch as arch
    from .windows import has_admin_privileges as has_admin_privileges
elif is_linux:  # pragma: no cover
    from .linux import arch as arch
    from .linux import has_admin_privileges as has_admin_privileges
elif is_macos:  # pragma: no cover
    from .macos import arch as arch
    from .macos import has_admin_privileges as has_admin_privileges
from . import capi as capi
from . import _limits as limits
