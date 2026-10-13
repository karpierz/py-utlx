# Copyright (c) 1994 Adam Karpierz
# SPDX-License-Identifier: Zlib

__all__ = ('arch', 'macos_version', 'capi', 'has_admin_privileges')

from . import capi
from ._arch import arch, macos_version
from ._util import has_admin_privileges
