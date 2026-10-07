# Copyright (c) 2004 Adam Karpierz
# SPDX-License-Identifier: Zlib

import unittest
import sys
import os
import platform
import types
import tempfile
import threading
import shutil
from pathlib import Path

import utlx
from utlx.imports import import_static, import_file, import_absolute
from utlx.platform import is_graalpy


class TestImportStatic(unittest.TestCase):

    def test_import_builtin_module(self):
        mod = import_static("math")
        self.assertIsInstance(mod, types.ModuleType)
        self.assertEqual(mod.__name__, "math")

    def test_import_with_reload(self):
        mod1 = import_static("enum")
        mod2 = import_static("enum", reload=True)
        self.assertIsInstance(mod2, types.ModuleType)
        self.assertEqual(mod2.__name__, "enum")
        self.assertIsNot(mod1, mod2)

    def test_import_nonexistent_module(self):
        with self.assertRaises(ImportError):
            import_static("nonexistent_module_abcxyz")


class TestImportFile(unittest.TestCase):

    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp())
        self.module_path = self.temp_dir/"testmod.py"
        self.module_path.write_text("x = 42\ny = 'hello'\n")

        # Package: directory with __init__.py
        self.pkg_dir = self.temp_dir/"mypkg"
        self.pkg_dir.mkdir()
        (self.pkg_dir/"__init__.py").write_text("a = 'package'\nb = 123\n")

        # Ensure temp_dir is in sys.path for strict_sys_path=True
        sys.path.insert(0, str(self.temp_dir))

    def tearDown(self):
        sys.path.remove(str(self.temp_dir))
        shutil.rmtree(self.temp_dir)

    def test_import_file_basic(self):
        mod = import_file(self.module_path)
        self.assertIsInstance(mod, types.ModuleType)
        self.assertEqual(mod.x, 42)
        self.assertEqual(mod.y, "hello")

    def test_import_file_with_custom_name(self):
        mod = import_file(self.module_path, name="custom_name")
        self.assertEqual(mod.__name__, "custom_name")

    def test_import_file_improper(self):
        module_path = self.temp_dir/"testmod.txt"
        module_path.write_text("\n")
        with self.assertRaises(ImportError):
            import_file(module_path)

    def test_import_file_reload(self):
        mod1 = import_file(self.module_path)
        mod2 = import_file(self.module_path, reload=True)
        self.assertIsNot(mod1, mod2)

    def test_import_file_strict_sys_path_violation(self):
        outside_path = Path(tempfile.gettempdir())/"outside.py"
        outside_path.write_text("z = 99\n")
        try:
            with self.assertRaises(ImportError):
                import_file(outside_path, strict_sys_path=True)
            # Default: strict_sys_path == True
            with self.assertRaises(ImportError):
                import_file(outside_path)
            import_file(outside_path, strict_sys_path=False)
        finally:
            outside_path.unlink()

    def test_import_file_nonexistent(self):
        with self.assertRaises(ImportError):
            import_file(self.temp_dir/"missing.py")

    def test_import_package_directory(self):
        mod = import_file(self.pkg_dir)
        self.assertIsInstance(mod, types.ModuleType)
        self.assertEqual(mod.a, "package")
        self.assertEqual(mod.b, 123)
        self.assertEqual(mod.__name__, "mypkg")

    def test_import_package_with_custom_name(self):
        mod = import_file(self.pkg_dir, name="custompkg")
        self.assertEqual(mod.__name__, "custompkg")

    def test_import_package_reload(self):
        mod1 = import_file(self.pkg_dir)
        mod2 = import_file(self.pkg_dir, reload=True)
        self.assertIsNot(mod1, mod2)

    def test_handles_non_path_entries(self):
        sys.path.insert(0, None)
        sys.path.insert(0, object())
        temp = Path(tempfile.mkdtemp()) / "mod.py"
        temp.write_text("x = 1\n")
        try:
            import_file(temp, strict_sys_path=True)
        except ImportError:
            pass  # expected
        finally:
            sys.path = [p for p in sys.path if isinstance(p, str)]
            shutil.rmtree(temp.parent)

    def test_handles_invalid_path_resolution(self):
        temp = Path(tempfile.mkdtemp()) / "mod.py"
        temp.write_text("x = 1\n")

        # Insert a value that makes Path(p) fail during sys.path scanning
        bad_entry = object()
        sys.path.insert(0, bad_entry)

        try:
            with self.assertRaisesRegex(ImportError,
                                        "Module path '.+' is not within "):
                import_file(temp)
        finally:
            sys.path.pop(0)
            shutil.rmtree(temp.parent)

    def test_handles_unresolvable_module_path(self):
        # Create a dummy object that will break Path(path)
        bad_path = object()

        # The function should raise ImportError when Path(path) fails
        with self.assertRaisesRegex(ImportError,
                                    "Cannot resolve module path"):
            import_file(bad_path)


class TestImportAbsolute(unittest.TestCase):

    def setUp(self):
        self.org_cwd = Path.cwd()
        self.cwd = Path(tempfile.mkdtemp())
        self.local_mod = self.cwd / "platform.py"
        self.local_mod.write_text("X = 123\n")
        self.temp_dir = Path(tempfile.mkdtemp())
        # symlink to CWD (if supported)
        self.symlink = self.temp_dir / "cwd_link"
        try:
            self.symlink.symlink_to(self.cwd, target_is_directory=True)
            self.symlink_supported = True
        except Exception:  # pragma: no cover
            self.symlink_supported = False
        os.chdir(self.cwd)

    def tearDown(self):
        if os.path.isdir(self.org_cwd):  # pragma: no branch
            os.chdir(self.org_cwd)
        shutil.rmtree(self.temp_dir)
        shutil.rmtree(self.cwd)

    def test_removes_empty_string(self):
        sys.path.insert(0, "")
        with utlx.imports.import_absolute():
            self.assertNotIn("", sys.path)
        self.assertIn("", sys.path)

    def test_removes_dot(self):
        sys.path.insert(0, ".")
        with utlx.imports.import_absolute():
            self.assertNotIn(".", sys.path)
        self.assertIn(".", sys.path)

    def test_removes_dot_slash(self):
        sys.path.insert(0, "./")
        with utlx.imports.import_absolute():
            self.assertNotIn("./", sys.path)
        self.assertIn("./", sys.path)

    def test_removes_absolute_cwd(self):
        sys.path.insert(0, str(self.cwd))
        with utlx.imports.import_absolute():
            self.assertNotIn(str(self.cwd), sys.path)
        self.assertIn(str(self.cwd), sys.path)

    def test_removes_symlink_to_cwd(self):
        if is_graalpy and not self.symlink_supported:
            self.skipTest("Symlinks not supported on this platform")  # pragma: no cover
        sys.path.insert(0, str(self.symlink))
        with utlx.imports.import_absolute():
            self.assertNotIn(str(self.symlink), sys.path)
        self.assertIn(str(self.symlink), sys.path)

    def test_does_not_remove_other_paths(self):
        sys.path.insert(0, "/usr")
        with utlx.imports.import_absolute():
            self.assertIn("/usr", sys.path)

    def test_restores_sys_path(self):
        original = sys.path.copy()
        with utlx.imports.import_absolute():
            pass
        self.assertEqual(sys.path, original)

    def test_import_ignores_local_shadowing(self):
        # local platform.py should NOT be imported
        with utlx.imports.import_absolute():
            import platform as p
        self.assertNotEqual(getattr(p, "__file__", ""), str(self.local_mod))

    def test_thread_safety(self):
        # sanity check: no crashes, no corruption
        def worker():
            for _ in range(100):
                with utlx.imports.import_absolute():
                    pass

        threads = [threading.Thread(target=worker) for _ in range(10)]
        for t in threads: t.start()
        for t in threads: t.join()

        self.assertTrue(True)  # if we got here, it's fine

    def test_handles_normalization_exception(self):
        sys.path.insert(0, None)
        with import_absolute():
            # None should trigger Exception in _normalize_path
            self.assertIn(None, sys.path)

    def test_handles_valueerror_on_remove(self):
        sys.path.insert(0, ".")
        with import_absolute():
            # simulate ValueError by removing manually before context
            try:
                sys.path.remove(".")
            except ValueError:
                pass
            # context should handle gracefully
            self.assertTrue(True)
