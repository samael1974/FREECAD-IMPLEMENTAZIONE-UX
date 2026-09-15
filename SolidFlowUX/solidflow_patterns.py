# -*- coding: utf-8 -*-
"""SolidFlow UX — Sketch/PartDesign pattern integration.

Restores and promotes the native FreeCAD pattern tools in the contextual S palette:
- Sketch edit mode: rectangular X/Y array and polar array/rotate.
- Part Design feature context: linear 3D and polar 3D patterns.

The implementation deliberately delegates creation to FreeCAD's native commands so
resulting geometry/features remain standard, editable FreeCAD objects.
"""

from __future__ import annotations

import FreeCAD as App
import FreeCADGui as Gui
from PySide import QtCore, QtWidgets

VERSION = "0.4.0-beta.8"

SKETCH_RECTANGULAR = "Sketcher_RectangularArray"
SKETCH_POLAR = "Sketcher_Rotate"
PD_LINEAR = "PartDesign_LinearPattern"
PD_POLAR = "PartDesign_PolarPattern"


def _command_available(command_id):
    try:
        return Gui.Command.get(command_id) is not None
    except Exception:
        return False


def _run_native(command_id):
    if not _command_available(command_id):
        QtWidgets.QMessageBox.warning(
            Gui.getMainWindow(),
            "SolidFlow — Serie",
            "Il comando FreeCAD '{}' non è disponibile nel contesto corrente.".format(command_id),
        )
        return
    try:
        Gui.runCommand(command_id, 0)
    except Exception as exc:
        App.Console.PrintError("SolidFlow pattern %s: %s\n" % (command_id, exc))


def _selected_internal_sketch_geometry_count():
    """Count selected internal EdgeN geometry while a sketch is in edit mode.

    ExternalEdgeN is intentionally excluded: native array/rotate operations should
    transform sketch-owned geometry, not external references.
    """
    count = 0
    try:
        edit = Gui.ActiveDocument.getInEdit() if Gui.ActiveDocument else None
        sketch = getattr(edit, "Object", None)
        if sketch is None and edit is not None:
            # Some FreeCAD builds return the ViewProvider itself.
            sketch = getattr(edit, "getObject", lambda: None)()
        for sx in Gui.Selection.getSelectionEx():
            if sketch is not None and getattr(sx, "Object", None) is not sketch:
                continue
            for name in list(getattr(sx, "SubElementNames", []) or []):
                text = str(name)
                if text.startswith("Edge") and not text.startswith("ExternalEdge"):
                    count += 1
    except Exception:
        return 0
    return count


def _insert_before_exit(smart, specs):
    """Insert pattern commands before workflow exit/reference actions."""
    result = list(smart)
    insert_at = len(result)
    exit_labels = {"Proietta", "Riferimenti faccia", "Chiudi Sketch"}
    for i, item in enumerate(result):
        if str(getattr(item, "label", "")) in exit_labels:
            insert_at = i
            break
    for spec in reversed(specs):
        result.insert(insert_at, spec)
    return result


def _patch_palette():
    try:
        import solidflow_ui as ui
    except Exception as exc:
        App.Console.PrintWarning("SolidFlow patterns: palette base non disponibile: %s\n" % exc)
        return False

    if getattr(ui, "_solidflow_patterns_patched", False):
        return True

    ActionSpec = ui.ActionSpec
    original_sketch = getattr(ui, "_sketch_groups", None)
    original_part = getattr(ui, "_partdesign_groups", None)
    if not callable(original_sketch) or not callable(original_part):
        App.Console.PrintWarning("SolidFlow patterns: hook palette non trovato.\n")
        return False

    def sketch_groups():
        title_a, stable, title_b, smart = original_sketch()
        if _selected_internal_sketch_geometry_count() > 0:
            pattern_specs = []
            if _command_available(SKETCH_RECTANGULAR):
                pattern_specs.append(
                    ActionSpec(
                        "Serie X/Y",
                        command=SKETCH_RECTANGULAR,
                        tooltip="Serie rettangolare nel piano dello Sketch: righe/colonne lungo X e Y",
                        icon_command=SKETCH_RECTANGULAR,
                        emphasis=True,
                    )
                )
            if _command_available(SKETCH_POLAR):
                pattern_specs.append(
                    ActionSpec(
                        "Serie polare",
                        command=SKETCH_POLAR,
                        tooltip="Ruota/copia la geometria selezionata creando una serie circolare",
                        icon_command=SKETCH_POLAR,
                        emphasis=True,
                    )
                )
            if pattern_specs:
                smart = _insert_before_exit(smart, pattern_specs)
                title_b = "VINCOLI / SERIE"
        return title_a, stable, title_b, smart

    def part_groups():
        title_a, stable, title_b, smart = original_part()
        try:
            kind = ui._selection_kind()
        except Exception:
            kind = ""
        if kind == "Feature":
            existing = {str(getattr(s, "label", "")) for s in smart}
            additions = []
            if "Serie lineare 3D" not in existing and _command_available(PD_LINEAR):
                additions.append(
                    ActionSpec(
                        "Serie lineare 3D",
                        command=PD_LINEAR,
                        tooltip="Ripete la feature lungo una direzione/asse; usa assi X, Y o Z del Body",
                        icon_command=PD_LINEAR,
                    )
                )
            if "Serie polare 3D" not in existing and _command_available(PD_POLAR):
                additions.append(
                    ActionSpec(
                        "Serie polare 3D",
                        command=PD_POLAR,
                        tooltip="Ripete la feature attorno a un asse del Body o riferimento selezionato",
                        icon_command=PD_POLAR,
                    )
                )
            if additions:
                smart = list(smart) + additions
        return title_a, stable, title_b, smart

    ui._solidflow_patterns_original_sketch_groups = original_sketch
    ui._solidflow_patterns_original_partdesign_groups = original_part
    ui._sketch_groups = sketch_groups
    ui._partdesign_groups = part_groups
    ui._solidflow_patterns_patched = True
    App.Console.PrintMessage(
        "SolidFlow %s: serie Sketch X/Y + polare e serie PartDesign 3D integrate.\n" % VERSION
    )
    return True


def _find_solidflow_menu():
    try:
        for menu in Gui.getMainWindow().findChildren(QtWidgets.QMenu):
            if menu.title().replace("&", "").strip().lower() == "solidflow":
                return menu
    except Exception:
        pass
    return None


def _augment_menu():
    menu = _find_solidflow_menu()
    if menu is None or menu.findChild(QtCore.QObject, "SolidFlowPatternsMarker"):
        return
    marker = QtCore.QObject(menu)
    marker.setObjectName("SolidFlowPatternsMarker")

    submenu = menu.addMenu("Serie & Trasformazioni")
    sketch_menu = submenu.addMenu("Dentro Sketch")
    a = sketch_menu.addAction("Serie rettangolare X/Y…")
    a.triggered.connect(lambda: _run_native(SKETCH_RECTANGULAR))
    a = sketch_menu.addAction("Serie polare…")
    a.triggered.connect(lambda: _run_native(SKETCH_POLAR))

    solid_menu = submenu.addMenu("Feature 3D")
    a = solid_menu.addAction("Serie lineare X/Y/Z…")
    a.triggered.connect(lambda: _run_native(PD_LINEAR))
    a = solid_menu.addAction("Serie polare 3D…")
    a.triggered.connect(lambda: _run_native(PD_POLAR))


class PatternController:
    def __init__(self):
        self._installed = False

    def install(self):
        if self._installed:
            return self
        _patch_palette()
        QtCore.QTimer.singleShot(700, _augment_menu)
        QtCore.QTimer.singleShot(1600, _augment_menu)
        self._installed = True
        return self


_controller = None


def install():
    global _controller
    app = QtWidgets.QApplication.instance()
    old = getattr(app, "_solidflow_patterns_controller", None) if app else None
    if old is not None and old is not _controller:
        # No timers/observers to tear down; keeping this branch documents reload ownership.
        pass
    if _controller is None or not getattr(_controller, "_installed", False):
        _controller = PatternController().install()
    if app:
        app._solidflow_patterns_controller = _controller
    return _controller
