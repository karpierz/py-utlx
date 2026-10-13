# Copyright (c) 1994 Adam Karpierz
# SPDX-License-Identifier: Zlib

__all__ = ('arch', 'capi', 'has_admin_privileges')

from . import capi
from ._arch import arch
from ._util import has_admin_privileges
