# flake8-in-file-ignores: noqa: A005,F401,F403,F405

# Copyright (c) 1994 Adam Karpierz
# SPDX-License-Identifier: Zlib

from ._detect import *
from ._oid    import *
from . import _limits as limits
if is_windows:  # pragma: no cover
    from .windows import *  # type: ignore[no-redef, unused-ignore]
elif is_linux:  # pragma: no cover
    from .linux import *    # type: ignore[no-redef, unused-ignore]
elif is_macos:  # pragma: no cover
    from .macos import *    # type: ignore[no-redef, unused-ignore]
