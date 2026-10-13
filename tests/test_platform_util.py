# Copyright (c) 2004 Adam Karpierz
# SPDX-License-Identifier: Zlib

import unittest
from unittest import mock
import sys
import os
import platform
import importlib

from utlx.platform import is_windows, is_linux, is_macos


@unittest.skipUnless(is_windows, "Windows-only tests")
class TestWindowsHasAdminPrivileges(unittest.TestCase):
    """Tests for has_admin_privileges() function on Windows."""

    def test_windows_has_admin_privileges_elevated(self):
        """Test Windows with elevated privileges (Vista+)."""
        from utlx.platform.windows import has_admin_privileges
        from utlx.platform.windows import winapi

        with mock.patch.object(sys, "getwindowsversion") as mock_win_ver:
            mock_win_ver.return_value = mock.Mock(major=10)  # Windows 10

            with mock.patch.object(winapi, "GetCurrentProcess") as mock_get_proc, \
                 mock.patch.object(winapi, "OpenProcessToken") as mock_open_token, \
                 mock.patch.object(winapi, "GetTokenInformation") as mock_get_token_info:

                # Setup mocks
                mock_get_proc.return_value = mock.Mock()
                mock_open_token.return_value = True
                mock_get_token_info.return_value = True

                # Mock the byref calls to modify elevation value
                def side_effect_byref(arg):
                    if hasattr(arg, "value"):  # pragma: no branch
                        arg.value = 1  # Elevated
                    return arg

                with mock.patch("ctypes.byref", side_effect=side_effect_byref):
                    result = has_admin_privileges()
                    self.assertTrue(result)

    def test_windows_has_admin_privileges_not_elevated(self):
        """Test Windows without elevated privileges (Vista+)."""
        from utlx.platform.windows import has_admin_privileges
        from utlx.platform.windows import winapi

        with mock.patch.object(sys, "getwindowsversion") as mock_win_ver:
            mock_win_ver.return_value = mock.Mock(major=10)  # Windows 10

            with mock.patch.object(winapi, "GetCurrentProcess") as mock_get_proc, \
                 mock.patch.object(winapi, "OpenProcessToken") as mock_open_token, \
                 mock.patch.object(winapi, "GetTokenInformation") as mock_get_token_info:

                # Setup mocks
                mock_get_proc.return_value = mock.Mock()
                mock_open_token.return_value = True
                mock_get_token_info.return_value = True

                # Mock the byref calls to modify elevation value
                def side_effect_byref(arg):
                    if hasattr(arg, "value"):  # pragma: no branch
                        arg.value = 0  # Not elevated
                    return arg

                with mock.patch("ctypes.byref", side_effect=side_effect_byref):
                    result = has_admin_privileges()
                    self.assertFalse(result)

    def test_windows_xp_has_admin_privileges_true(self):
        """Test Windows XP/2003 with admin privileges."""
        from utlx.platform.windows import has_admin_privileges
        from utlx.platform.windows import winapi

        with mock.patch.object(sys, "getwindowsversion") as mock_win_ver:
            mock_win_ver.return_value = mock.Mock(major=5)  # Windows XP/2003

            with mock.patch.object(winapi.windll.shell32, "IsUserAnAdmin") as mock_is_admin:
                mock_is_admin.return_value = True
                result = has_admin_privileges()
                self.assertTrue(result)

    def test_windows_xp_has_admin_privileges_false(self):
        """Test Windows XP/2003 without admin privileges."""
        from utlx.platform.windows import has_admin_privileges
        from utlx.platform.windows import winapi

        with mock.patch.object(sys, "getwindowsversion") as mock_win_ver:
            mock_win_ver.return_value = mock.Mock(major=5)  # Windows XP/2003

            with mock.patch.object(winapi.windll.shell32, "IsUserAnAdmin") as mock_is_admin:
                mock_is_admin.return_value = False
                result = has_admin_privileges()
                self.assertFalse(result)

    def test_windows_open_process_token_fails(self):
        """Test Windows when OpenProcessToken fails."""
        from utlx.platform.windows import has_admin_privileges
        from utlx.platform.windows import winapi

        with mock.patch.object(sys, "getwindowsversion") as mock_win_ver:
            mock_win_ver.return_value = mock.Mock(major=10)  # Windows 10

            with mock.patch.object(winapi, "OpenProcessToken") as mock_open_token:
                mock_open_token.return_value = False
                result = has_admin_privileges()
                self.assertFalse(result)

    def test_windows_get_token_information_fails(self):
        """Test Windows when GetTokenInformation fails."""
        from utlx.platform.windows import has_admin_privileges
        from utlx.platform.windows import winapi

        with mock.patch.object(sys, "getwindowsversion") as mock_win_ver:
            mock_win_ver.return_value = mock.Mock(major=10)  # Windows 10

            with mock.patch.object(winapi, "GetCurrentProcess"), \
                 mock.patch.object(winapi, "OpenProcessToken") as mock_open_token, \
                 mock.patch.object(winapi, "GetTokenInformation") as mock_get_token_info:

                mock_open_token.return_value = True
                mock_get_token_info.return_value = False
                result = has_admin_privileges()
                self.assertFalse(result)


@unittest.skipUnless(is_linux, "Linux-only tests")
class TestLinuxHasAdminPrivileges(unittest.TestCase):
    """Tests for has_admin_privileges() function on Linux."""

    def test_linux_has_admin_privileges_root(self):
        """Test Linux with root privileges (UID == 0)."""
        from utlx.platform.linux import has_admin_privileges

        with mock.patch.object(os, "getuid", return_value=0):
            result = has_admin_privileges()
            self.assertTrue(result)

    def test_linux_has_admin_privileges_not_root(self):
        """Test Linux without root privileges (UID != 0)."""
        from utlx.platform.linux import has_admin_privileges

        with mock.patch.object(os, "getuid", return_value=1000):
            result = has_admin_privileges()
            self.assertFalse(result)

    def test_linux_no_getuid_attribute(self):
        """Test Linux when getuid is not available."""
        from utlx.platform.linux import has_admin_privileges

        with mock.patch.object(os, "getuid", side_effect=AttributeError):
            result = has_admin_privileges()
            self.assertFalse(result)


@unittest.skipUnless(is_macos, "macOS-only tests")
class TestMacOSHasAdminPrivileges(unittest.TestCase):
    """Tests for has_admin_privileges() function on macOS."""

    def test_macos_has_admin_privileges_root(self):
        """Test macOS with root privileges (UID == 0)."""
        from utlx.platform.macos import has_admin_privileges

        with mock.patch.object(os, "getuid", return_value=0):
            result = has_admin_privileges()
            self.assertTrue(result)

    def test_macos_has_admin_privileges_not_root(self):
        """Test macOS without root privileges (UID != 0)."""
        from utlx.platform.macos import has_admin_privileges

        with mock.patch.object(os, "getuid", return_value=501):  # Standard user on macOS
            result = has_admin_privileges()
            self.assertFalse(result)

    def test_macos_no_getuid_attribute(self):
        """Test macOS when getuid is not available."""
        from utlx.platform.macos import has_admin_privileges

        with mock.patch.object(os, "getuid", side_effect=AttributeError):
            result = has_admin_privileges()
            self.assertFalse(result)
