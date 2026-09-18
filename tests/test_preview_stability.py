"""Fast regression tests; Qt is real, FreeCAD document objects are test doubles."""
import os
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace as NS

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'SolidFlowUX'))
from solidflow_preview import PreviewTransaction, set_feature_sides


class Feature:
    def __init__(self, modern=True):
        self.PropertiesList = ['Reversed', 'SideType' if modern else 'Midplane']
        self.modern = modern

    def __setattr__(self, key, value):
        if key == 'Midplane' and getattr(self, 'modern', False):
            raise AssertionError('deprecated Midplane write')
        super().__setattr__(key, value)


def obj(name, visible):
    return NS(Name=name, ViewObject=NS(Visibility=visible))


class Document:
    def __init__(self):
        self.seed, self.sketch = obj('Pad', True), obj('Sketch', False)
        self.body = obj('Body', True)
        self.body.Group = [self.seed, self.sketch]
        self.body.Tip = self.seed
        self.objects = {o.Name: o for o in [self.seed, self.sketch, self.body, obj('Other', True)]}
        self.calls = []

    def getObject(self, name):
        return self.objects.get(name)

    def openTransaction(self, label):
        self.calls.append('begin')
        self.before = set(self.objects)

    def abortTransaction(self):
        self.calls.append('abort')
        self.objects = {n: o for n, o in self.objects.items() if n in self.before}

    def commitTransaction(self):
        self.calls.append('commit')

    def recompute(self):
        self.calls.append('recompute')


class PreviewTests(unittest.TestCase):
    def test_modern_and_legacy_side_modes(self):
        for modern in (True, False):
            for symmetric in (True, False):
                for reverse in (True, False):
                    with self.subTest(modern=modern, symmetric=symmetric, reverse=reverse):
                        f = Feature(modern)
                        set_feature_sides(f, symmetric, reverse)
                        self.assertEqual(f.Reversed, reverse)
                        self.assertEqual(f.SideType if modern else f.Midplane,
                                         ('Symmetric' if symmetric else 'One side') if modern else symmetric)

    def test_20_cancel_cycles_restore_tip_and_visibility_without_touching_other(self):
        doc = Document()
        for _ in range(20):
            tx = PreviewTransaction(doc, [doc.sketch], doc.body)
            tx.begin('preview')
            doc.objects['Preview'] = obj('Preview', True)
            doc.body.Tip = doc.objects['Preview']
            doc.seed.ViewObject.Visibility = False
            doc.sketch.ViewObject.Visibility = True
            doc.objects['Other'].ViewObject.Visibility = False
            tx.rollback()
            tx.rollback()  # close after Cancel is harmless
            self.assertNotIn('Preview', doc.objects)
            self.assertIs(doc.body.Tip, doc.seed)
            self.assertTrue(doc.seed.ViewObject.Visibility)
            self.assertFalse(doc.sketch.ViewObject.Visibility)
            self.assertFalse(doc.objects['Other'].ViewObject.Visibility)
        self.assertEqual(doc.calls.count('abort'), 20)

    def test_commit_retains_native_visibility_and_tip(self):
        doc = Document()
        tx = PreviewTransaction(doc, [doc.seed], doc.body)
        tx.begin('preview')
        doc.seed.ViewObject.Visibility = False
        tx.commit()
        tx.rollback()
        self.assertFalse(doc.seed.ViewObject.Visibility)
        self.assertEqual(doc.calls, ['begin', 'commit'])

    def test_abort_failure_is_not_silenced(self):
        doc = Document()
        tx = PreviewTransaction(doc)
        tx.begin('preview')
        def fail():
            raise RuntimeError('abort failed')
        doc.abortTransaction = fail
        with self.assertRaises(RuntimeError):
            tx.rollback()
        self.assertTrue(tx.active)


try:
    from PySide6 import QtCore, QtWidgets
except ImportError:
    QtWidgets = None


@unittest.skipIf(QtWidgets is None, 'PySide6 required for real Qt event tests')
class ViewbarTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
        cls.enabled = True
        cls.fc = NS(ParamGet=lambda _: NS(GetBool=lambda *args: cls.enabled))
        cls.gui = NS(ActiveDocument=object())
        sys.modules['FreeCAD'] = cls.fc
        sys.modules['FreeCADGui'] = cls.gui
        sys.modules['PySide'] = NS(QtCore=QtCore, QtWidgets=QtWidgets)
        import solidflow_viewbar
        cls.module = solidflow_viewbar

    def setUp(self):
        type(self).enabled = True
        self.gui.ActiveDocument = object()
        self.main = QtWidgets.QMainWindow()
        self.mdi = QtWidgets.QMdiArea()
        self.main.setCentralWidget(self.mdi)
        self.main.resize(1000, 800)
        self.main.show()
        self.first = self.add_view()
        self.bar = self.module.DisplayStyleBar(self.main)
        self.bar.sync_position()
        self.pump()

    def add_view(self):
        sub = self.mdi.addSubWindow(QtWidgets.QWidget())
        sub.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        sub.showMaximized()
        self.mdi.setActiveSubWindow(sub)
        return sub

    def pump(self):
        for _ in range(8):
            self.app.processEvents()
        QtCore.QCoreApplication.sendPostedEvents(None, QtCore.QEvent.DeferredDelete)
        self.app.processEvents()

    def tearDown(self):
        self.main.close()
        self.main.deleteLater()
        self.pump()

    def test_document_close_does_not_destroy_bar(self):
        second = self.add_view()
        self.pump()
        second.close()
        self.pump()
        self.assertIs(self.bar.parent(), self.main)
        self.assertTrue(self.bar.isVisible())
        self.assertEqual(len(self.main.findChildren(QtWidgets.QFrame, 'SolidFlowDisplayStyleBar')), 1)

    def test_resize_and_maximize_restore_repositions_without_polling(self):
        old = self.bar.pos()
        self.main.resize(1200, 900)
        self.pump()
        self.assertNotEqual(self.bar.pos(), old)
        self.first.showNormal()
        self.pump()
        self.first.showMaximized()
        self.pump()
        self.assertTrue(self.bar.isVisible())

    def test_no_document_and_disabled_preference_hide(self):
        self.gui.ActiveDocument = None
        self.bar.sync_position()
        self.assertFalse(self.bar.isVisible())

        self.gui.ActiveDocument = object()
        type(self).enabled = False
        self.bar.sync_position()
        self.assertFalse(self.bar.isVisible())

    def test_cancel_before_deferred_begin_creates_no_feature(self):
        import solidflow_features
        doc = Document()
        doc.sketch.Document = doc
        doc.sketch.Label = 'Sketch'
        original = solidflow_features._body_for
        solidflow_features._body_for = lambda _: doc.body
        try:
            dialog = solidflow_features.FeaturePreviewDialog('pad', doc.sketch, parent=self.main)
            dialog.reject()
            self.pump()
            self.assertEqual(doc.calls, [])
            self.assertIsNone(dialog.feature)
        finally:
            solidflow_features._body_for = original


if __name__ == '__main__':
    unittest.main()
