# -*- coding: utf-8 -*-
"""SolidFlow smart Sketcher helpers: snap tuning and context-aware constraint suggestions."""
import math

import FreeCAD as App
import FreeCADGui as Gui
from PySide import QtCore, QtWidgets

PREF_PATH = "User parameter:BaseApp/Preferences/Mod/SolidFlowUX"
SKETCH_GENERAL_PATH = "User parameter:BaseApp/Preferences/Mod/Sketcher/General"


def _prefs():
    return App.ParamGet(PREF_PATH)


def _sketch_general():
    return App.ParamGet(SKETCH_GENERAL_PATH)


def smart_snap_enabled():
    return _prefs().GetBool("SmartSnapEnabled", True)


def constraint_hints_enabled():
    return _prefs().GetBool("ConstraintHintsEnabled", True)


def smart_snap_delay():
    return max(0, min(1000, _prefs().GetInt("SmartSnapDelay", 150)))


def set_smart_snap_enabled(enabled):
    enabled = bool(enabled)
    _prefs().SetBool("SmartSnapEnabled", enabled)
    if enabled:
        apply_smart_snap_preferences()
    else:
        restore_native_snap_delay()


def set_constraint_hints_enabled(enabled):
    _prefs().SetBool("ConstraintHintsEnabled", bool(enabled))


def set_smart_snap_delay(value):
    value = max(0, min(1000, int(value)))
    _prefs().SetInt("SmartSnapDelay", value)
    if smart_snap_enabled():
        _sketch_general().SetInt("DragAutoConstraintDelay", value)


def apply_smart_snap_preferences():
    """Use FreeCAD's own auto-constraint engine, tuned for a quicker response."""
    if not smart_snap_enabled():
        return
    grp = _sketch_general()
    p = _prefs()
    if not p.GetBool("SavedOriginalDragAutoConstraintDelay", False):
        p.SetInt("OriginalDragAutoConstraintDelay", grp.GetInt("DragAutoConstraintDelay", 400))
        p.SetBool("SavedOriginalDragAutoConstraintDelay", True)
    grp.SetInt("DragAutoConstraintDelay", smart_snap_delay())
    ensure_current_sketch_autoconstraints()


def restore_native_snap_delay():
    p = _prefs()
    if p.GetBool("SavedOriginalDragAutoConstraintDelay", False):
        _sketch_general().SetInt(
            "DragAutoConstraintDelay",
            p.GetInt("OriginalDragAutoConstraintDelay", 400),
        )


def ensure_current_sketch_autoconstraints():
    """Turn on Sketcher's native auto-constraint flag for the sketch currently in edit mode."""
    if not smart_snap_enabled():
        return False
    try:
        if not Gui.ActiveDocument:
            return False
        vp = Gui.ActiveDocument.getInEdit()
        if vp is None:
            return False
        if hasattr(vp, "Autoconstraints"):
            try:
                vp.Autoconstraints = True
                return True
            except Exception:
                pass
        # Some builds expose it through the ViewObject returned by the edited object.
        obj = getattr(vp, "Object", None)
        view = getattr(obj, "ViewObject", None) if obj else None
        if view is not None and hasattr(view, "Autoconstraints"):
            view.Autoconstraints = True
            return True
    except Exception:
        pass
    return False


def _command_available(name):
    try:
        cmd = Gui.Command.get(name)
        if not cmd:
            return False
        actions = cmd.getAction()
        if not actions:
            return True
        return bool(actions[0].isEnabled())
    except Exception:
        return False


def _selection_ex():
    try:
        return Gui.Selection.getSelectionEx()
    except Exception:
        return []


def _single_selected_sketch_item():
    sel = _selection_ex()
    if len(sel) != 1:
        return None
    item = sel[0]
    obj = getattr(item, "Object", None)
    if obj is None:
        return None
    try:
        if not obj.isDerivedFrom("Sketcher::SketchObject"):
            return None
    except Exception:
        if getattr(obj, "TypeId", "") != "Sketcher::SketchObject":
            return None
    return item


def selected_geometry_info():
    """Best-effort geometry descriptors for selected Sketch edges.

    We deliberately use this only to *rank suggestions*. The actual constraint is always
    executed by FreeCAD's native command on the real selection, so a descriptor mismatch
    cannot directly create an invalid constraint.
    """
    item = _single_selected_sketch_item()
    if item is None:
        return None, []
    sketch = item.Object
    names = [str(n) for n in (getattr(item, "SubElementNames", []) or []) if str(n).startswith("Edge")]
    result = []
    for name in names:
        try:
            idx = int(name[4:]) - 1
        except Exception:
            continue
        geo = None
        try:
            if 0 <= idx < len(sketch.Geometry):
                geo = sketch.Geometry[idx]
        except Exception:
            geo = None
        result.append((name, idx, geo))
    return sketch, result


def _vec2(point):
    try:
        return float(point.x), float(point.y)
    except Exception:
        return None


def _line_data(geo):
    if geo is None:
        return None
    try:
        a = _vec2(geo.StartPoint)
        b = _vec2(geo.EndPoint)
        if a is None or b is None:
            return None
        dx, dy = b[0] - a[0], b[1] - a[1]
        length = math.hypot(dx, dy)
        if length <= 1e-12:
            return None
        return {"a": a, "b": b, "dx": dx, "dy": dy, "length": length}
    except Exception:
        return None


def _circle_data(geo):
    if geo is None:
        return None
    try:
        radius = float(geo.Radius)
        center = _vec2(geo.Center)
        if radius <= 0 or center is None:
            return None
        return {"radius": radius, "center": center}
    except Exception:
        return None


def _distance(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


def _suggest(label, command, reason, score):
    if not _command_available(command):
        return None
    return {
        "label": label,
        "command": command,
        "reason": reason,
        "score": float(score),
    }


def constraint_suggestions(limit=5):
    """Return context-aware Sketcher constraint suggestions, highest confidence first."""
    sketch, geos = selected_geometry_info()
    if sketch is None or not geos:
        return []

    suggestions = []
    if len(geos) == 1:
        geo = geos[0][2]
        line = _line_data(geo)
        circ = _circle_data(geo)
        if line:
            ratio_h = abs(line["dy"]) / max(line["length"], 1e-9)
            ratio_v = abs(line["dx"]) / max(line["length"], 1e-9)
            if ratio_h < 0.12:
                suggestions.append(_suggest("Orizzontale", "Sketcher_ConstrainHorizontal", "La linea è quasi orizzontale", 100 - ratio_h * 100))
            if ratio_v < 0.12:
                suggestions.append(_suggest("Verticale", "Sketcher_ConstrainVertical", "La linea è quasi verticale", 100 - ratio_v * 100))
            suggestions.append(_suggest("Lunghezza", "Sketcher_ConstrainDistance", "Quota la lunghezza della linea", 45))
            suggestions.append(_suggest("Blocca", "Sketcher_ConstrainLock", "Blocca la geometria selezionata", 15))
        elif circ:
            suggestions.append(_suggest("Diametro", "Sketcher_ConstrainDiameter", "Quota il diametro", 65))
            suggestions.append(_suggest("Raggio", "Sketcher_ConstrainRadius", "Quota il raggio", 55))
            suggestions.append(_suggest("Blocca", "Sketcher_ConstrainLock", "Blocca la geometria selezionata", 15))
        else:
            suggestions.append(_suggest("Quota", "Sketcher_ConstrainDistance", "Aggiungi una quota", 30))

    elif len(geos) == 2:
        g1, g2 = geos[0][2], geos[1][2]
        l1, l2 = _line_data(g1), _line_data(g2)
        c1, c2 = _circle_data(g1), _circle_data(g2)
        if l1 and l2:
            u1 = (l1["dx"] / l1["length"], l1["dy"] / l1["length"])
            u2 = (l2["dx"] / l2["length"], l2["dy"] / l2["length"])
            dot = abs(u1[0] * u2[0] + u1[1] * u2[1])
            cross = abs(u1[0] * u2[1] - u1[1] * u2[0])
            if cross < math.sin(math.radians(10)):
                suggestions.append(_suggest("Parallelo", "Sketcher_ConstrainParallel", "Le linee sono quasi parallele", 100 - cross * 100))
            if dot < math.sin(math.radians(10)):
                suggestions.append(_suggest("Perpendicolare", "Sketcher_ConstrainPerpendicular", "Le linee sono quasi a 90°", 100 - dot * 100))
            rel = abs(l1["length"] - l2["length"]) / max((l1["length"] + l2["length"]) * 0.5, 1e-9)
            if rel < 0.12:
                suggestions.append(_suggest("Uguale", "Sketcher_ConstrainEqual", "Le linee hanno lunghezze molto simili", 90 - rel * 100))
            endpoints1 = (l1["a"], l1["b"])
            endpoints2 = (l2["a"], l2["b"])
            near = min(_distance(a, b) for a in endpoints1 for b in endpoints2)
            scale = max(l1["length"], l2["length"], 1e-9)
            if near / scale < 0.08:
                suggestions.append(_suggest("Coincidente", "Sketcher_ConstrainCoincident", "Due estremità sono molto vicine", 92 - (near / scale) * 100))
            # Keep common relations available even when geometry is not already almost there.
            suggestions.append(_suggest("Parallelo", "Sketcher_ConstrainParallel", "Rendi parallele le linee", 25))
            suggestions.append(_suggest("Perpendicolare", "Sketcher_ConstrainPerpendicular", "Rendi perpendicolari le linee", 24))
            suggestions.append(_suggest("Uguale", "Sketcher_ConstrainEqual", "Rendi uguali le lunghezze", 23))
        elif (l1 and c2) or (c1 and l2):
            suggestions.append(_suggest("Tangente", "Sketcher_ConstrainTangent", "Linea e arco/cerchio possono essere resi tangenti", 80))
        elif c1 and c2:
            rel = abs(c1["radius"] - c2["radius"]) / max((c1["radius"] + c2["radius"]) * 0.5, 1e-9)
            if rel < 0.12:
                suggestions.append(_suggest("Uguale", "Sketcher_ConstrainEqual", "I raggi sono molto simili", 90 - rel * 100))
            suggestions.append(_suggest("Tangente", "Sketcher_ConstrainTangent", "Rendi tangenti i cerchi/archi", 35))
            suggestions.append(_suggest("Uguale", "Sketcher_ConstrainEqual", "Rendi uguali i raggi", 30))
        else:
            suggestions.append(_suggest("Coincidente", "Sketcher_ConstrainCoincident", "Vincola punti coincidenti", 30))
    else:
        suggestions.append(_suggest("Uguale", "Sketcher_ConstrainEqual", "Applica uguaglianza alle geometrie compatibili", 45))
        suggestions.append(_suggest("Coincidente", "Sketcher_ConstrainCoincident", "Vincola punti compatibili", 30))

    # Drop unavailable suggestions, remove duplicates, then rank by confidence.
    dedup = {}
    for s in suggestions:
        if not s:
            continue
        prev = dedup.get(s["command"])
        if prev is None or s["score"] > prev["score"]:
            dedup[s["command"]] = s
    ordered = sorted(dedup.values(), key=lambda s: (-s["score"], s["label"]))
    return ordered[: max(1, int(limit))]


def apply_best_constraint():
    suggestions = constraint_suggestions(limit=1)
    if not suggestions:
        return False
    try:
        Gui.runCommand(suggestions[0]["command"])
        return True
    except Exception as exc:
        App.Console.PrintWarning("[SolidFlowUX] Smart constraint failed: {}\n".format(exc))
        return False


class SmartSketchSettingsDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent or Gui.getMainWindow())
        self.setWindowTitle("SolidFlow - Smart Sketch")
        self.resize(430, 230)
        root = QtWidgets.QVBoxLayout(self)
        root.setContentsMargins(14, 14, 14, 14)
        root.setSpacing(10)

        intro = QtWidgets.QLabel(
            "SolidFlow usa il motore AutoConstraint nativo di FreeCAD e aggiunge suggerimenti "
            "contestuali senza imporre automaticamente vincoli rischiosi.",
            self,
        )
        intro.setWordWrap(True)
        root.addWidget(intro)

        self.snap = QtWidgets.QCheckBox("Smart Snap / AutoConstraint reattivo", self)
        self.snap.setChecked(smart_snap_enabled())
        root.addWidget(self.snap)

        row = QtWidgets.QHBoxLayout()
        row.addWidget(QtWidgets.QLabel("Ritardo suggerimento snap", self))
        self.delay = QtWidgets.QSpinBox(self)
        self.delay.setRange(0, 1000)
        self.delay.setSingleStep(25)
        self.delay.setSuffix(" ms")
        self.delay.setValue(smart_snap_delay())
        row.addWidget(self.delay)
        row.addStretch(1)
        root.addLayout(row)

        self.hints = QtWidgets.QCheckBox("Mostra automaticamente i vincoli suggeriti vicino al cursore", self)
        self.hints.setChecked(constraint_hints_enabled())
        root.addWidget(self.hints)

        note = QtWidgets.QLabel(
            "Suggerimenti: orizzontale/verticale, coincidente, uguale, parallelo, "
            "perpendicolare, tangente e quote, in base alla geometria selezionata.",
            self,
        )
        note.setWordWrap(True)
        root.addWidget(note)

        buttons = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel,
            parent=self,
        )
        root.addWidget(buttons)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

    def accept(self):
        set_smart_snap_enabled(self.snap.isChecked())
        set_smart_snap_delay(self.delay.value())
        set_constraint_hints_enabled(self.hints.isChecked())
        if self.snap.isChecked():
            apply_smart_snap_preferences()
        super().accept()


_open_settings = []


def show_smart_sketch_settings():
    dlg = SmartSketchSettingsDialog()
    _open_settings.append(dlg)
    dlg.finished.connect(lambda _r, d=dlg: _open_settings.remove(d) if d in _open_settings else None)
    dlg.show()
    dlg.raise_()
    dlg.activateWindow()
