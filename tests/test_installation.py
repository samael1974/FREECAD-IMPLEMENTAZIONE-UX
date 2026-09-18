import ast
import base64
import hashlib
import importlib.util
import io
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import patch
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, str(path))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


support = module('install_support', ROOT / 'installer/install_support.py')
builder = module('tester_builder', ROOT / 'tools/build_tester_package.py')
diagnostics = module('diagnostics', ROOT / 'SolidFlowUX/solidflow_diagnostics.py')


class InstallationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.build_dir = tempfile.TemporaryDirectory()
        package = builder.build(cls.build_dir.name)
        with zipfile.ZipFile(package) as z:
            source = z.read('SolidFlowUX-Installa.FCMacro')
        values = {n.targets[0].id: ast.literal_eval(n.value) for n in ast.parse(source).body
                  if isinstance(n, ast.Assign) and isinstance(n.targets[0], ast.Name)}
        cls.payload = base64.b64decode(values['PAYLOAD'])
        cls.digest = values['PAYLOAD_SHA256']

    @classmethod
    def tearDownClass(cls):
        cls.build_dir.cleanup()

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / 'Profilo portabile con spazi à'
        self.root.mkdir()
        self.target = self.root / 'Mod/SolidFlowUX'

    def install(self, **kwargs):
        return support.install_runtime(self.payload, self.digest, self.root, 'test', **kwargs)

    def old_copy(self):
        self.target.mkdir(parents=True)
        (self.target / 'InitGui.py').write_text('old')
        (self.target / 'personal.txt').write_text('preserve in backup')
        (self.target / 'unins000.exe').write_bytes(b'uninstaller')

    def test_first_install_exact_profile_and_complete_runtime(self):
        result = self.install()
        self.assertEqual(Path(result['target']), self.target)
        self.assertIsNone(result['backup'])
        names = support.unpack_runtime(self.payload, self.digest)
        for name, content in names.items():
            self.assertEqual((self.target / name).read_bytes(), content)
            self.assertEqual(content, (ROOT / 'SolidFlowUX' / name).read_bytes())

    def test_upgrade_preserves_backup_and_uninstaller(self):
        self.old_copy()
        result = self.install()
        backup = Path(result['backup'])
        self.assertEqual((backup / 'InitGui.py').read_text(), 'old')
        self.assertEqual((backup / 'personal.txt').read_text(), 'preserve in backup')
        self.assertEqual((self.target / 'unins000.exe').read_bytes(), b'uninstaller')
        self.assertNotIn('Mod', backup.relative_to(self.root).parts)

    def test_failed_swap_restores_old_copy(self):
        import os
        self.old_copy()
        def replace(src, dst):
            if Path(src).name.startswith('.solidflow-stage-'):
                raise PermissionError('injected final rename failure')
            os.replace(src, dst)
        with self.assertRaises(PermissionError):
            self.install(replace=replace)
        self.assertEqual((self.target / 'InitGui.py').read_text(), 'old')
        self.assertEqual((self.target / 'personal.txt').read_text(), 'preserve in backup')
        self.assertFalse(list(self.root.glob('.solidflow-stage-*')))

    def test_failed_backup_leaves_original_untouched(self):
        self.old_copy()
        def fail(*args):
            raise PermissionError('injected backup failure')
        with self.assertRaises(PermissionError):
            self.install(replace=fail)
        self.assertEqual((self.target / 'InitGui.py').read_text(), 'old')

    def test_corrupt_payload_does_not_create_destination(self):
        with self.assertRaises(ValueError):
            support.install_runtime(self.payload + b'bad', self.digest, self.root, 'test')
        self.assertFalse(self.target.parent.exists())

    def test_unrelated_profile_is_untouched(self):
        other = Path(self.temp.name) / 'Other/Mod/SolidFlowUX'
        other.mkdir(parents=True)
        marker = other / 'InitGui.py'
        marker.write_text('other profile')
        self.install()
        self.assertEqual(marker.read_text(), 'other profile')

    def test_archive_traversal_is_rejected(self):
        data = io.BytesIO()
        with zipfile.ZipFile(data, 'w') as archive:
            archive.writestr('../escape.py', 'unsafe')
        blob = data.getvalue()
        with self.assertRaises(ValueError):
            support.unpack_runtime(blob, hashlib.sha256(blob).hexdigest())

    def test_diagnostics_works_before_addon_loads(self):
        app = types.SimpleNamespace(getUserAppDataDir=lambda: str(self.root), Version=lambda: ['1', '1', '0'])
        with patch.dict(sys.modules, {'solidflow_ui': None}):
            report = diagnostics.collect_report(app)
        self.assertIn('NON CARICATA', report)
        self.assertIn('Manifest: ASSENTE', report)
        self.assertIn('FreeCAD: 1.1.0', report)

    def test_diagnostics_detects_incomplete_install(self):
        self.install()
        (self.target / 'solidflow_smart.py').unlink()
        app = types.SimpleNamespace(getUserAppDataDir=lambda: str(self.root), Version=lambda: ['1', '1', '0'])
        with patch.dict(sys.modules, {'solidflow_ui': None}):
            self.assertIn('MANCANTI: solidflow_smart.py', diagnostics.collect_report(app))

    def test_installer_lists_every_manifest_module(self):
        text = (ROOT / 'installer/SolidFlowUX.iss').read_text(encoding='utf-8-sig')
        for name in support.unpack_runtime(self.payload, self.digest):
            self.assertIn('SolidFlowUX\\' + name, text)
        self.assertIn('DisableDirPage=no', text)
        self.assertIn('function PrepareToInstall', text)


class LazyCommandTests(unittest.TestCase):
    def test_commands_become_available_after_sketcher_loads(self):
        registry = {}
        app = types.ModuleType('FreeCAD')
        gui = types.ModuleType('FreeCADGui')
        gui.Command = types.SimpleNamespace(get=registry.get)
        qt = types.ModuleType('PySide')
        qt.QtCore = types.SimpleNamespace()
        qt.QtWidgets = types.SimpleNamespace(QDialog=object)
        with patch.dict(sys.modules, {'FreeCAD': app, 'FreeCADGui': gui, 'PySide': qt}):
            smart = module('smart_test', ROOT / 'SolidFlowUX/solidflow_smart.py')
            self.assertEqual(smart.all_constraint_actions(), [])
            registry['Sketcher_ConstrainDistance'] = object()
            self.assertIn(('Lunghezza / distanza', 'Sketcher_ConstrainDistance'), smart.all_constraint_actions())
            registry.clear()
            self.assertEqual(smart.all_constraint_actions(), [])


if __name__ == '__main__':
    unittest.main()
