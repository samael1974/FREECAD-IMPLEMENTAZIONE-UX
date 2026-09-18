# -*- coding: utf-8 -*-
"""SolidFlow UX core PartDesign helpers (beta.9 stabilization).

Creates native FreeCAD PartDesign features.  The module intentionally keeps the
public function names used by the older SolidFlow palette/layers so updates can
be installed over beta.3-beta.8 without breaking imports.
"""
from __future__ import annotations

import FreeCAD as App
import FreeCADGui as Gui
from PySide import QtCore, QtWidgets

from solidflow_preview import PreviewTransaction, set_feature_sides

PREF_PATH = "User parameter:BaseApp/Preferences/Mod/SolidFlowUX"


def _prefs():
    return App.ParamGet(PREF_PATH)


def auto_face_references_enabled():
    return _prefs().GetBool("AutoFaceReferences", True)


def set_auto_face_references_enabled(enabled):
    _prefs().SetBool("AutoFaceReferences", bool(enabled))


def _main_window():
    return Gui.getMainWindow()


def _warning(title, text):
    QtWidgets.QMessageBox.warning(_main_window(), title, text)


def _is_sketch(obj):
    try:
        return bool(obj and obj.isDerivedFrom("Sketcher::SketchObject"))
    except Exception:
        return getattr(obj, "TypeId", "") == "Sketcher::SketchObject"


def _body_for(obj):
    if obj is None:
        return None
    try:
        parent = obj.getParentGeoFeatureGroup()
        if parent and parent.isDerivedFrom("PartDesign::Body"):
            return parent
    except Exception:
        pass
    doc = getattr(obj, "Document", None)
    if doc:
        for candidate in doc.Objects:
            try:
                if candidate.isDerivedFrom("PartDesign::Body") and obj in list(candidate.Group):
                    return candidate
            except Exception:
                pass
    return None


def selection_snapshot():
    try:
        return Gui.Selection.getSelectionEx()
    except Exception:
        return []


def selected_face():
    sel = selection_snapshot()
    if len(sel) != 1:
        return None
    item = sel[0]
    faces = [str(n) for n in list(getattr(item, "SubElementNames", []) or []) if str(n).startswith("Face")]
    return (item.Object, faces[0]) if len(faces) == 1 else None


def _active_edit_sketch():
    try:
        if not Gui.ActiveDocument:
            return None
        edit = Gui.ActiveDocument.getInEdit()
        obj = getattr(edit, "Object", None) if edit else None
        return obj if _is_sketch(obj) else None
    except Exception:
        return None


def selected_profile():
    """Return (Sketch, selected EdgeN list); active edit mode uses whole sketch.

    Ignoring incidental selected edges while editing fixes a common failure where
    Pad/Pocket received only one edge of an otherwise closed profile.
    Explicit sub-edge profiles remain available when selecting a Sketch outside
    edit mode.
    """
    edit_sketch = _active_edit_sketch()
    sel = selection_snapshot()
    if len(sel) == 1 and _is_sketch(sel[0].Object):
        obj = sel[0].Object
        if edit_sketch is obj:
            return obj, []
        names = list(getattr(sel[0], "SubElementNames", []) or [])
        return obj, [str(n) for n in names if str(n).startswith("Edge")]
    if edit_sketch is not None:
        return edit_sketch, []
    return None, []


def selected_sketch_objects():
    try:
        return [o for o in Gui.Selection.getSelection() if _is_sketch(o)]
    except Exception:
        return []


def selected_editable_feature():
    try:
        objs = Gui.Selection.getSelection()
    except Exception:
        return None
    if len(objs) != 1:
        return None
    obj = objs[0]
    return obj if getattr(obj, "TypeId", "") in (
        "PartDesign::Pad", "PartDesign::Pocket", "PartDesign::Revolution"
    ) else None


def _face_edge_names(support, face_name):
    try:
        shape = support.Shape
        face = shape.getElement(face_name)
    except Exception:
        try:
            shape = support.Shape
            face = shape.Faces[int(face_name[4:]) - 1]
        except Exception:
            return []
    result = []
    for fedge in list(getattr(face, "Edges", []) or []):
        for idx, edge in enumerate(list(shape.Edges), 1):
            try:
                same = fedge.isSame(edge)
            except Exception:
                try:
                    same = fedge.isEqual(edge)
                except Exception:
                    same = False
            if same:
                name = "Edge%d" % idx
                if name not in result:
                    result.append(name)
                break
    return result


def _add_face_external_refs(sketch, support, face_name):
    added, failed = [], []
    existing = set()
    try:
        for info in list(getattr(sketch, "ExternalGeometry", []) or []):
            try:
                existing.add((str(info[0]), str(info[1])))
            except Exception:
                pass
    except Exception:
        pass
    for edge_name in _face_edge_names(support, face_name):
        key = (support.Name, edge_name)
        if key in existing:
            continue
        try:
            sketch.addExternal(support.Name, edge_name)
            added.append(edge_name)
        except Exception as exc:
            failed.append((edge_name, str(exc)))
    try:
        sketch.Document.recompute()
    except Exception:
        pass
    return added, failed


def create_sketch_on_face():
    found = selected_face()
    if not found:
        _warning("SolidFlow", "Seleziona una sola faccia planare, poi riprova.")
        return None
    support, face_name = found
    body = _body_for(support)
    if body is None:
        _warning("SolidFlow", "La faccia selezionata deve appartenere a un Body Part Design.")
        return None
    doc = support.Document
    doc.openTransaction("SolidFlow - Sketch on face")
    sketch = None
    try:
        sketch = body.newObject("Sketcher::SketchObject", "Sketch")
        sketch.AttachmentSupport = [(support, face_name)]
        sketch.MapMode = "FlatFace"
        doc.recompute()
        if auto_face_references_enabled():
            _add_face_external_refs(sketch, support, face_name)
        doc.commitTransaction()
    except Exception as exc:
        try:
            doc.abortTransaction()
        except Exception:
            pass
        _warning("SolidFlow", "Creazione dello Sketch fallita:\n%s" % exc)
        return None
    try:
        Gui.Selection.clearSelection()
        Gui.Selection.addSelection(sketch)
        Gui.ActiveDocument.setEdit(sketch.Name)
    except Exception as exc:
        App.Console.PrintWarning("SolidFlow: Sketch creato ma apertura edit fallita: %s\n" % exc)
    return sketch


def add_support_face_references_to_active_sketch():
    sketch = _active_edit_sketch()
    if sketch is None:
        _warning("SolidFlow", "Apri prima uno Sketch mappato su una faccia.")
        return
    try:
        support_info = sketch.AttachmentSupport
        support = support_info[0][0]
        sub = support_info[0][1]
        face_name = sub[0] if isinstance(sub, (list, tuple)) else str(sub)
    except Exception:
        _warning("SolidFlow", "Non riesco a determinare la faccia di supporto dello Sketch.")
        return
    added, failed = _add_face_external_refs(sketch, support, face_name)
    App.Console.PrintMessage("SolidFlow: riferimenti aggiunti=%d, errori=%d\n" % (len(added), len(failed)))


def show_closed_profiles():
    sketch, _ = selected_profile()
    if sketch is None:
        _warning("SolidFlow", "Seleziona uno Sketch.")
        return
    try:
        wires = list(sketch.Shape.Wires)
    except Exception:
        wires = []
    QtWidgets.QMessageBox.information(
        _main_window(), "SolidFlow - Profili",
        "Profili/wire rilevati nello Sketch: %d\n\nLe regioni cliccabili arriveranno in una fase successiva." % len(wires),
    )


def _shape_valid(feature):
    try:
        if not feature.isValid():
            return False
    except Exception:
        pass
    try:
        return feature.Shape is not None and not feature.Shape.isNull() and feature.Shape.isValid()
    except Exception:
        return False


class FeaturePreviewDialog(QtWidgets.QDialog):
    """Modal, transaction-safe preview for Pad/Pocket/basic Revolution."""
    def __init__(self, mode, sketch, subs=None, parent=None):
        super().__init__(parent or _main_window())
        self.mode, self.sketch, self.subs = mode, sketch, list(subs or [])
        self.doc = sketch.Document
        self.body = _body_for(sketch)
        self.feature = None
        self._tx = False
        self._accepted = False
        self._closed = False
        self._preview = PreviewTransaction(self.doc, [sketch], self.body)
        title = {"pad":"Estrusione solida", "pocket":"Taglio estruso", "revolution":"Rivoluzione solida"}[mode]
        self.setWindowTitle("SolidFlow - " + title)
        self.setModal(True)
        self.resize(430, 310)
        root = QtWidgets.QVBoxLayout(self)
        root.addWidget(QtWidgets.QLabel("<b>%s</b>" % title))
        root.addWidget(QtWidgets.QLabel("Profilo: %s%s" % (
            sketch.Label, " — contorni selezionati" if self.subs else " — intero Sketch")))
        form = QtWidgets.QFormLayout(); root.addLayout(form)
        self.value = QtWidgets.QDoubleSpinBox(); self.value.setDecimals(3); self.value.setKeyboardTracking(False)
        if mode == "revolution":
            self.value.setRange(0.1, 360.0); self.value.setValue(360.0); self.value.setSuffix(" °")
            form.addRow("Angolo", self.value)
            self.axis = QtWidgets.QComboBox(); self.axis.addItem("Verticale Sketch", "V_Axis"); self.axis.addItem("Orizzontale Sketch", "H_Axis")
            form.addRow("Asse", self.axis)
        else:
            self.value.setRange(0.01, 1000000.0); self.value.setValue(10.0); self.value.setSuffix(" mm")
            form.addRow("Profondità" if mode == "pocket" else "Lunghezza", self.value)
            self.axis = None
        self.reversed = QtWidgets.QCheckBox("Inverti direzione")
        self.midplane = QtWidgets.QCheckBox("Simmetrica rispetto allo Sketch")
        root.addWidget(self.reversed); root.addWidget(self.midplane)
        self.status = QtWidgets.QLabel("Preparazione anteprima…"); self.status.setWordWrap(True); root.addWidget(self.status)
        box = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        root.addWidget(box); self.ok = box.button(QtWidgets.QDialogButtonBox.Ok); self.ok.setEnabled(False)
        box.accepted.connect(self.accept); box.rejected.connect(self.reject)
        self.value.valueChanged.connect(self.update_preview)
        self.reversed.toggled.connect(self.update_preview); self.midplane.toggled.connect(self.update_preview)
        if self.axis: self.axis.currentIndexChanged.connect(self.update_preview)
        QtCore.QTimer.singleShot(0, self._begin)

    def _begin(self):
        if self._closed:
            return
        if self.body is None:
            self.status.setText("Lo Sketch deve appartenere a un Body Part Design."); return
        try:
            self._preview.begin("SolidFlow preview"); self._tx = True
            type_id = {"pad":"PartDesign::Pad", "pocket":"PartDesign::Pocket", "revolution":"PartDesign::Revolution"}[self.mode]
            self.feature = self.body.newObject(type_id, "SolidFlow" + self.mode.title())
            self.feature.Profile = (self.sketch, self.subs) if self.subs else self.sketch
            try: self.feature.ViewObject.Transparency = 55
            except Exception: pass
            self.update_preview()
        except Exception as exc:
            self.status.setText("Errore anteprima: %s" % exc); self._rollback()

    def update_preview(self, *_args):
        if self.feature is None: return
        try:
            if self.mode in ("pad", "pocket"):
                self.feature.Length = float(self.value.value())
            else:
                self.feature.Angle = float(self.value.value())
                self.feature.ReferenceAxis = (self.sketch, [self.axis.currentData()])
            set_feature_sides(self.feature, self.midplane.isChecked(), self.reversed.isChecked())
            self.doc.recompute()
            valid = _shape_valid(self.feature)
            self.ok.setEnabled(valid)
            self.status.setText("✓ Anteprima valida" if valid else "⚠ Operazione non valida: controlla profilo e direzione")
        except Exception as exc:
            self.ok.setEnabled(False); self.status.setText("⚠ Anteprima non valida: %s" % exc)

    def _rollback(self):
        self._closed = True
        self._preview.rollback()
        self._tx = False
        self.feature = None

    def accept(self):
        if not self.feature or not self.ok.isEnabled(): return
        try:
            self.feature.ViewObject.Transparency = 0
            self.doc.recompute()
            if not _shape_valid(self.feature):
                raise RuntimeError("La feature non produce una geometria valida")
            if self._tx: self._preview.commit(); self._tx = False
            self._accepted = True
            super().accept()
        except Exception as exc:
            _warning("SolidFlow", "Conferma feature fallita:\n%s" % exc)

    def reject(self):
        if not self._accepted: self._rollback()
        super().reject()

    def closeEvent(self, event):
        if not self._accepted: self._rollback()
        super().closeEvent(event)


def _finish_edit_and_select(sketch, callback):
    if _active_edit_sketch() is sketch:
        try: Gui.ActiveDocument.resetEdit()
        except Exception:
            try: Gui.runCommand("Sketcher_LeaveSketch", 0)
            except Exception: pass
        try:
            Gui.Selection.clearSelection(); Gui.Selection.addSelection(sketch)
        except Exception: pass
        QtCore.QTimer.singleShot(120, callback)
        return True
    return False


def _launch(mode):
    sketch, subs = selected_profile()
    if sketch is None:
        _warning("SolidFlow", "Seleziona oppure modifica uno Sketch, poi riprova.")
        return
    if _finish_edit_and_select(sketch, lambda m=mode: _launch(m)):
        return
    dlg = FeaturePreviewDialog(mode, sketch, subs)
    dlg.exec_()


def launch_pad(): _launch("pad")
def launch_pocket(): _launch("pocket")
def launch_revolution(): _launch("revolution")


def launch_sweep():
    try:
        import solidflow_beta6
        solidflow_beta6._launch_sweep(False)
        return
    except Exception:
        pass
    _warning("SolidFlow - Sweep", "La funzione Sweep avanzata non è caricata. Controlla Diagnostica SolidFlow.")


class QuickEditFeatureDialog(QtWidgets.QDialog):
    def __init__(self, feature, parent=None):
        super().__init__(parent or _main_window())
        self.feature = feature; self.doc = feature.Document; self._tx = False; self._old = {}
        self.setWindowTitle("SolidFlow - Modifica rapida: " + feature.Label); self.setModal(True)
        lay = QtWidgets.QVBoxLayout(self); form = QtWidgets.QFormLayout(); lay.addLayout(form)
        self.value = QtWidgets.QDoubleSpinBox(); self.value.setDecimals(3); self.value.setKeyboardTracking(False)
        is_rev = feature.TypeId == "PartDesign::Revolution"
        prop = "Angle" if is_rev else "Length"; self.prop = prop
        try: current = float(getattr(feature, prop).Value)
        except Exception: current = float(getattr(feature, prop))
        self._old[prop] = current
        self.value.setRange(0.1 if is_rev else 0.01, 360.0 if is_rev else 1000000.0); self.value.setValue(current); self.value.setSuffix(" °" if is_rev else " mm")
        form.addRow("Angolo" if is_rev else "Valore", self.value)
        box = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel); lay.addWidget(box)
        box.accepted.connect(self.accept); box.rejected.connect(self.reject); self.value.valueChanged.connect(self.preview)
        self.doc.openTransaction("SolidFlow Quick Edit"); self._tx = True
    def preview(self, value):
        try: setattr(self.feature, self.prop, float(value)); self.doc.recompute()
        except Exception: pass
    def accept(self):
        try:
            self.doc.recompute(); self.doc.commitTransaction(); self._tx=False
        except Exception: pass
        super().accept()
    def reject(self):
        if self._tx:
            try: self.doc.abortTransaction()
            except Exception: pass
            self._tx=False
        super().reject()


def launch_edit_selected_feature():
    feature = selected_editable_feature()
    if feature is None: return False
    QuickEditFeatureDialog(feature).exec_(); return True
