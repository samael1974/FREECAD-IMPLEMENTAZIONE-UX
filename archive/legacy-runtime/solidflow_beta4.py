# -*- coding: utf-8 -*-
"""SolidFlow UX v0.4 beta.4 additions.

This module is intentionally additive: it sits on top of the existing beta.3
without replacing PartDesign/Sketcher logic already provided by solidflow_ui.

Features:
- contextual Quick Constraints near the cursor while editing a Sketch;
- prioritised tangent/collinear, concentric/coincident, parallel,
  perpendicular, equal, horizontal/vertical and dimensional constraints;
- native FreeCAD Sketcher commands are used for the actual constraint;
- SolidWorks-like light 3D/sketch colour preset, with persistent backup;
- faster native drag auto-constraint suggestions;
- idempotent install/uninstall hooks and a small SolidFlow menu extension.
"""

from __future__ import annotations

import FreeCAD as App
import FreeCADGui as Gui
from PySide import QtCore, QtGui, QtWidgets

VERSION = "0.4.0-beta.4"

ROOT = App.ParamGet("User parameter:BaseApp/Preferences/Mod/SolidFlowUX")
VIEW = App.ParamGet("User parameter:BaseApp/Preferences/View")
SKETCH_GENERAL = App.ParamGet("User parameter:BaseApp/Preferences/Mod/Sketcher/General")
THEME_BACKUP = App.ParamGet(
    "User parameter:BaseApp/Preferences/Mod/SolidFlowUX/ThemeBackup"
)
SMART_BACKUP = App.ParamGet(
    "User parameter:BaseApp/Preferences/Mod/SolidFlowUX/SmartSketchBackup"
)


def _rgba(r: int, g: int, b: int, a: int = 255) -> int:
    """FreeCAD packed RGBA colour (RRGGBBAA)."""
    return ((r & 255) << 24) | ((g & 255) << 16) | ((b & 255) << 8) | (a & 255)


_THEME_BOOL = {
    "Gradient": True,
    "RadialGradient": False,
    "Simple": False,
    "UseBackgroundColorMid": False,
}

# Light blue/grey 3D canvas + Sketch colours inspired by the visual hierarchy
# familiar from SolidWorks. No proprietary icons/assets are used.
_THEME_UINT = {
    # 3D viewport
    "BackgroundColor": _rgba(224, 232, 239),
    "BackgroundColor2": _rgba(111, 143, 171),
    "BackgroundColor3": _rgba(232, 238, 244),
    "BackgroundColor4": _rgba(248, 250, 252),
    "DefaultShapeColor": _rgba(210, 215, 220),
    "DefaultShapeLineColor": _rgba(55, 62, 68),
    "DefaultShapeVertexColor": _rgba(55, 62, 68),
    "HighlightColor": _rgba(255, 176, 0),
    "SelectionColor": _rgba(0, 153, 204),
    "AxisLetterColor": _rgba(40, 45, 50),
    "AnnotationTextColor": _rgba(35, 40, 45),
    # Sketch: under-defined blue, fully-defined near black, invalid red.
    "SketchEdgeColor": _rgba(38, 103, 189),
    "SketchVertexColor": _rgba(38, 103, 189),
    "EditedEdgeColor": _rgba(38, 103, 189),
    "FullyConstrainedColor": _rgba(35, 35, 35),
    "FullyConstraintElementColor": _rgba(35, 35, 35),
    "FullyConstraintConstructionElementColor": _rgba(90, 105, 120),
    "ConstructionColor": _rgba(105, 135, 165),
    "ExternalColor": _rgba(176, 72, 184),
    "ExternalDefiningColor": _rgba(176, 72, 184),
    "InvalidSketchColor": _rgba(210, 45, 45),
    "InternalAlignedGeoColor": _rgba(95, 110, 125),
    "ConstrainedIcoColor": _rgba(55, 60, 65),
    "ConstrainedDimColor": _rgba(55, 60, 65),
    "NonDrivingConstrDimColor": _rgba(75, 125, 155),
    "ExprBasedConstrDimColor": _rgba(95, 75, 145),
    "DeactivatedConstrDimColor": _rgba(135, 140, 145),
    "CursorTextColor": _rgba(25, 30, 35),
    "CursorCrosshairColor": _rgba(40, 45, 50),
    "CreateLineColor": _rgba(38, 103, 189),
}


def _backup_theme_once() -> None:
    if THEME_BACKUP.GetBool("Stored", False):
        return
    for key in _THEME_BOOL:
        THEME_BACKUP.SetBool("b_" + key, VIEW.GetBool(key, False))
    for key in _THEME_UINT:
        THEME_BACKUP.SetUnsigned("u_" + key, VIEW.GetUnsigned(key, 0))
    THEME_BACKUP.SetBool("Stored", True)


def apply_sw_like_theme() -> None:
    """Apply the reversible SolidFlow/SolidWorks-like visual preset."""
    _backup_theme_once()
    for key, value in _THEME_BOOL.items():
        VIEW.SetBool(key, value)
    for key, value in _THEME_UINT.items():
        VIEW.SetUnsigned(key, value)
    ROOT.SetBool("SWLikeTheme", True)
    try:
        Gui.updateGui()
    except Exception:
        pass
    App.Console.PrintMessage("SolidFlow: tema SolidWorks-like applicato.\n")


def restore_previous_theme() -> None:
    """Restore the colours that were present before SolidFlow first changed them."""
    if not THEME_BACKUP.GetBool("Stored", False):
        App.Console.PrintWarning("SolidFlow: nessun backup tema disponibile.\n")
        return
    for key in _THEME_BOOL:
        VIEW.SetBool("" + key, THEME_BACKUP.GetBool("b_" + key, False))
    for key in _THEME_UINT:
        VIEW.SetUnsigned("" + key, THEME_BACKUP.GetUnsigned("u_" + key, 0))
    ROOT.SetBool("SWLikeTheme", False)
    try:
        Gui.updateGui()
    except Exception:
        pass
    App.Console.PrintMessage("SolidFlow: aspetto FreeCAD precedente ripristinato.\n")


def _configure_native_smart_snap() -> None:
    """Make FreeCAD's own drag auto-constraint suggestions more responsive."""
    if not SMART_BACKUP.GetBool("Stored", False):
        SMART_BACKUP.SetInt(
            "DragAutoConstraintDelay",
            SKETCH_GENERAL.GetInt("DragAutoConstraintDelay", 400),
        )
        SMART_BACKUP.SetBool("Stored", True)
    # 150 ms feels immediate but still avoids noisy accidental suggestions.
    SKETCH_GENERAL.SetInt("DragAutoConstraintDelay", 150)


# ---------------------------------------------------------------------------
# Sketch helpers
# ---------------------------------------------------------------------------


def _active_sketch():
    try:
        if not Gui.ActiveDocument:
            return None
        edit = Gui.ActiveDocument.getInEdit()
        if edit and edit.isDerivedFrom("SketcherGui::ViewProviderSketch"):
            return edit.Object
    except Exception:
        pass
    return None


def _ensure_autoconstraints(sketch) -> None:
    if sketch is None:
        return
    try:
        vp = sketch.ViewObject
        if hasattr(vp, "Autoconstraints"):
            vp.Autoconstraints = True
    except Exception:
        pass


def _command_exists(command_id: str) -> bool:
    try:
        return Gui.Command.get(command_id) is not None
    except Exception:
        return False


def _first_command(*candidates: str) -> str | None:
    for cmd in candidates:
        if _command_exists(cmd):
            return cmd
    return None


CMD = {
    "coincident": _first_command(
        "Sketcher_ConstrainCoincidentUnified", "Sketcher_ConstrainCoincident"
    ),
    "point_on": _first_command("Sketcher_ConstrainPointOnObject"),
    "horver": _first_command("Sketcher_ConstrainHorVer"),
    "horizontal": _first_command("Sketcher_ConstrainHorizontal"),
    "vertical": _first_command("Sketcher_ConstrainVertical"),
    "parallel": _first_command("Sketcher_ConstrainParallel"),
    "perpendicular": _first_command("Sketcher_ConstrainPerpendicular"),
    "tangent": _first_command("Sketcher_ConstrainTangent"),
    "equal": _first_command("Sketcher_ConstrainEqual"),
    "symmetric": _first_command("Sketcher_ConstrainSymmetric"),
    "distance": _first_command("Sketcher_ConstrainDistance"),
    "distance_x": _first_command("Sketcher_ConstrainDistanceX"),
    "distance_y": _first_command("Sketcher_ConstrainDistanceY"),
    "radius": _first_command("Sketcher_ConstrainRadius"),
    "diameter": _first_command("Sketcher_ConstrainDiameter"),
    "angle": _first_command("Sketcher_ConstrainAngle"),
}


def _curve_kind(sub_object, sub_name: str) -> str:
    name = (sub_name or "").lower()
    if name.startswith("vertex") or "rootpoint" in name:
        return "vertex"
    if "axis" in name:
        return "line"
    if name.startswith("edge") or "externaledge" in name:
        try:
            curve = sub_object.Curve
            t = type(curve).__name__.lower()
            if "circle" in t or "ellipse" in t:
                return "circle"
            if "line" in t:
                return "line"
            if "arc" in t:
                return "curve"
        except Exception:
            pass
        return "edge"
    return "other"


def _selected_items(sketch):
    """Return [(subName, SubObject, semanticKind), ...] for the edited sketch."""
    result = []
    try:
        for sx in Gui.Selection.getSelectionEx():
            if sx.Object != sketch:
                continue
            names = list(getattr(sx, "SubElementNames", []) or [])
            subs = list(getattr(sx, "SubObjects", []) or [])
            for i, name in enumerate(names):
                sub = subs[i] if i < len(subs) else None
                result.append((name, sub, _curve_kind(sub, name)))
    except Exception:
        return []
    return result


def _add_suggestion(out, label, key, tip, accent=False):
    cmd = CMD.get(key)
    if not cmd:
        return
    if any(existing[1] == cmd for existing in out):
        return
    out.append((label, cmd, tip, accent))


def _suggestions(items):
    """Return prioritised constraint buttons for the current selection."""
    out = []
    n = len(items)
    kinds = [item[2] for item in items]

    if n == 1:
        kind = kinds[0]
        if kind == "circle":
            _add_suggestion(out, "Raggio", "radius", "Imposta il raggio")
            _add_suggestion(out, "Diametro", "diameter", "Imposta il diametro")
        elif kind == "line":
            _add_suggestion(
                out,
                "H/V",
                "horver",
                "FreeCAD sceglie automaticamente Orizzontale o Verticale",
                True,
            )
            _add_suggestion(out, "Orizz.", "horizontal", "Vincolo orizzontale")
            _add_suggestion(out, "Vert.", "vertical", "Vincolo verticale")
            _add_suggestion(out, "Quota", "distance", "Quota la lunghezza")
        elif kind == "vertex":
            _add_suggestion(out, "X", "distance_x", "Quota coordinata X")
            _add_suggestion(out, "Y", "distance_y", "Quota coordinata Y")

    elif n == 2:
        pair = set(kinds)
        if pair == {"circle", "line"} or pair == {"circle", "edge"}:
            # This is the high-priority use case requested for a circle against
            # an automatically projected/external edge of the supporting face.
            _add_suggestion(
                out,
                "Tangente",
                "tangent",
                "Rende tangente cerchio/arco e bordo, anche se il bordo è geometria esterna",
                True,
            )
            _add_suggestion(out, "Punto su", "point_on", "Punto su oggetto, quando applicabile")
            _add_suggestion(out, "Quota", "distance", "Distanza tra gli elementi")
        elif kinds.count("circle") == 2:
            _add_suggestion(
                out,
                "Concentrico",
                "coincident",
                "Coincidenza unificata: con due cerchi propone la concentricità",
                True,
            )
            _add_suggestion(out, "Tangente", "tangent", "Tangente tra cerchi/archi")
            _add_suggestion(out, "Uguale", "equal", "Raggi uguali")
        elif kinds.count("line") == 2 or pair <= {"line", "edge"}:
            _add_suggestion(
                out,
                "Collin./Tang.",
                "tangent",
                "Il comando nativo applica collinearità alle linee o tangenza alle curve",
                True,
            )
            _add_suggestion(out, "Parallelo", "parallel", "Linee parallele")
            _add_suggestion(out, "Perpend.", "perpendicular", "Linee perpendicolari")
            _add_suggestion(out, "Uguale", "equal", "Lunghezze uguali")
        elif "vertex" in pair and ("line" in pair or "edge" in pair):
            _add_suggestion(out, "Punto su", "point_on", "Vincola il punto alla geometria", True)
            _add_suggestion(out, "Coincidente", "coincident", "Coincidenza unificata")
            _add_suggestion(out, "Quota", "distance", "Distanza")
        elif kinds.count("vertex") == 2:
            _add_suggestion(out, "Coincidente", "coincident", "Unisce i due punti", True)
            _add_suggestion(out, "Orizz.", "horizontal", "Allinea orizzontalmente")
            _add_suggestion(out, "Vert.", "vertical", "Allinea verticalmente")
            _add_suggestion(out, "Quota", "distance", "Distanza tra i punti")
        else:
            _add_suggestion(out, "Coincidente", "coincident", "Coincidenza / concentricità", True)
            _add_suggestion(out, "Tangente", "tangent", "Tangenza / collinearità")
            _add_suggestion(out, "Uguale", "equal", "Rende uguali gli elementi")
            _add_suggestion(out, "Quota", "distance", "Distanza")

    elif n == 3:
        _add_suggestion(out, "Simmetria", "symmetric", "Vincolo di simmetria", True)
        _add_suggestion(out, "Coincidente", "coincident", "Coincidenza unificata")
        _add_suggestion(out, "Uguale", "equal", "Rende uguali gli elementi")

    elif n > 3:
        _add_suggestion(out, "Uguale", "equal", "Rende uguali gli elementi compatibili")
        _add_suggestion(out, "Parallelo", "parallel", "Rende parallele le linee selezionate")

    return out[:4]


_ALL_CONSTRAINTS = [
    ("Coincidente / Concentrico", "coincident"),
    ("Punto su oggetto", "point_on"),
    ("Orizzontale / Verticale auto", "horver"),
    ("Orizzontale", "horizontal"),
    ("Verticale", "vertical"),
    ("Parallelo", "parallel"),
    ("Perpendicolare", "perpendicular"),
    ("Tangente / Collineare", "tangent"),
    ("Uguale", "equal"),
    ("Simmetria", "symmetric"),
    ("Distanza", "distance"),
    ("Distanza X", "distance_x"),
    ("Distanza Y", "distance_y"),
    ("Raggio", "radius"),
    ("Diametro", "diameter"),
    ("Angolo", "angle"),
]


class QuickConstraintBar(QtWidgets.QFrame):
    def __init__(self, controller):
        flags = QtCore.Qt.Tool | QtCore.Qt.FramelessWindowHint
        super().__init__(Gui.getMainWindow(), flags)
        self.controller = controller
        self._signature = None
        self.setObjectName("SolidFlowQuickConstraints")
        self.setAttribute(QtCore.Qt.WA_ShowWithoutActivating, True)
        self.setFocusPolicy(QtCore.Qt.NoFocus)
        self.setStyleSheet(
            "QFrame#SolidFlowQuickConstraints {"
            " background: rgba(245,247,249,246); border:1px solid #8a9cab;"
            " border-radius:6px; }"
            "QToolButton { min-height:30px; padding:3px 7px; border:0;"
            " border-radius:4px; color:#20262b; font-size:11px; }"
            "QToolButton:hover { background:#dce9f3; }"
            "QToolButton[accent='true'] { background:#d4e8f7; font-weight:600; }"
        )
        self.layout = QtWidgets.QHBoxLayout(self)
        self.layout.setContentsMargins(5, 4, 5, 4)
        self.layout.setSpacing(3)

    def _clear(self):
        while self.layout.count():
            item = self.layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

    def _button(self, label, cmd, tip, accent=False):
        btn = QtWidgets.QToolButton(self)
        btn.setText(label)
        btn.setToolButtonStyle(QtCore.Qt.ToolButtonTextBesideIcon)
        btn.setToolTip(tip)
        btn.setFocusPolicy(QtCore.Qt.NoFocus)
        btn.setProperty("accent", "true" if accent else "false")
        try:
            native = Gui.Command.get(cmd)
            actions = native.getAction() if native else []
            if actions:
                btn.setIcon(actions[0].icon())
                btn.setIconSize(QtCore.QSize(18, 18))
        except Exception:
            pass
        btn.clicked.connect(lambda checked=False, c=cmd: self.controller.run_constraint(c))
        return btn

    def rebuild(self, suggestions):
        sig = tuple((s[0], s[1]) for s in suggestions)
        if sig == self._signature:
            return
        self._signature = sig
        self._clear()
        for label, cmd, tip, accent in suggestions:
            self.layout.addWidget(self._button(label, cmd, tip, accent))

        more = QtWidgets.QToolButton(self)
        more.setText("⋯")
        more.setToolTip("Altri vincoli")
        more.setFocusPolicy(QtCore.Qt.NoFocus)
        more.clicked.connect(self.controller.show_all_constraints)
        self.layout.addWidget(more)
        self.adjustSize()

    def show_near_cursor(self):
        self.adjustSize()
        pos = QtGui.QCursor.pos() + QtCore.QPoint(18, 22)
        screen = QtWidgets.QApplication.screenAt(QtGui.QCursor.pos())
        if screen:
            area = screen.availableGeometry()
            x = min(pos.x(), area.right() - self.width() - 8)
            y = min(pos.y(), area.bottom() - self.height() - 8)
            pos = QtCore.QPoint(max(area.left() + 8, x), max(area.top() + 8, y))
        self.move(pos)
        self.show()
        self.raise_()


class _SelectionObserver:
    def __init__(self, controller):
        self.controller = controller

    def addSelection(self, *args):
        self.controller.schedule_update()

    def removeSelection(self, *args):
        self.controller.schedule_update()

    def clearSelection(self, *args):
        self.controller.schedule_update()

    def setSelection(self, *args):
        self.controller.schedule_update()


class SmartSketchController:
    def __init__(self):
        self.observer = _SelectionObserver(self)
        self.bar = QuickConstraintBar(self)
        self._installed = False
        self._menu_actions = []
        self.timer = QtCore.QTimer()
        self.timer.setSingleShot(True)
        self.timer.setInterval(55)
        self.timer.timeout.connect(self.update)

    @property
    def enabled(self):
        return ROOT.GetBool("QuickConstraints", True)

    def set_enabled(self, state: bool):
        ROOT.SetBool("QuickConstraints", bool(state))
        if not state:
            self.bar.hide()
        self.schedule_update()

    def schedule_update(self):
        if self._installed:
            self.timer.start()

    def update(self):
        if not self.enabled:
            self.bar.hide()
            return
        sketch = _active_sketch()
        if sketch is None:
            self.bar.hide()
            return
        _ensure_autoconstraints(sketch)
        items = _selected_items(sketch)
        suggestions = _suggestions(items)
        if not suggestions:
            self.bar.hide()
            return
        self.bar.rebuild(suggestions)
        self.bar.show_near_cursor()

    def run_constraint(self, command_id: str):
        self.bar.hide()
        try:
            Gui.runCommand(command_id, 0)
            Gui.updateGui()
        except Exception as exc:
            App.Console.PrintError(
                "SolidFlow Quick Constraints - %s: %s\n" % (command_id, exc)
            )
        QtCore.QTimer.singleShot(90, self.schedule_update)

    def show_all_constraints(self):
        menu = QtWidgets.QMenu(self.bar)
        menu.setStyleSheet("QMenu { font-size:11px; padding:4px; }")
        for label, key in _ALL_CONSTRAINTS:
            cmd = CMD.get(key)
            if not cmd:
                continue
            action = menu.addAction(label)
            try:
                native = Gui.Command.get(cmd)
                actions = native.getAction() if native else []
                if actions:
                    action.setIcon(actions[0].icon())
            except Exception:
                pass
            action.triggered.connect(lambda checked=False, c=cmd: self.run_constraint(c))
        menu.exec_(QtGui.QCursor.pos())

    def _augment_menu(self):
        main = Gui.getMainWindow()
        target = None
        for menu in main.findChildren(QtWidgets.QMenu):
            title = menu.title().replace("&", "").strip().lower()
            if title == "solidflow":
                target = menu
                break
        if target is None:
            return
        if target.findChild(QtCore.QObject, "SolidFlowBeta4Marker"):
            return

        marker = QtCore.QObject(target)
        marker.setObjectName("SolidFlowBeta4Marker")
        target.addSeparator()

        quick = target.addAction("Vincoli rapidi contestuali")
        quick.setCheckable(True)
        quick.setChecked(self.enabled)
        quick.toggled.connect(self.set_enabled)
        self._menu_actions.append(quick)

        theme = target.addAction("Tema SolidWorks-like")
        theme.setCheckable(True)
        theme.setChecked(ROOT.GetBool("SWLikeTheme", True))

        def toggle_theme(state):
            if state:
                apply_sw_like_theme()
            else:
                restore_previous_theme()

        theme.toggled.connect(toggle_theme)
        self._menu_actions.append(theme)

        restore = target.addAction("Ripristina aspetto precedente")
        restore.triggered.connect(restore_previous_theme)
        self._menu_actions.append(restore)

    def install(self):
        if self._installed:
            return
        _configure_native_smart_snap()
        Gui.Selection.addObserver(self.observer)
        self._installed = True
        if ROOT.GetBool("SWLikeTheme", True):
            apply_sw_like_theme()
        QtCore.QTimer.singleShot(700, self._augment_menu)
        QtCore.QTimer.singleShot(1200, self._augment_menu)
        self.schedule_update()
        App.Console.PrintMessage(
            "SolidFlow UX %s: Smart Sketch / Quick Constraints attivi.\n" % VERSION
        )

    def uninstall(self):
        if not self._installed:
            return
        try:
            Gui.Selection.removeObserver(self.observer)
        except Exception:
            pass
        self.timer.stop()
        self.bar.hide()
        self.bar.deleteLater()
        self._installed = False


_controller = None


def install():
    global _controller
    app = QtWidgets.QApplication.instance()
    old = getattr(app, "_solidflow_beta4_controller", None) if app else None
    if old is not None and old is not _controller:
        try:
            old.uninstall()
        except Exception:
            pass
    if _controller is None or not getattr(_controller, "_installed", False):
        _controller = SmartSketchController()
        _controller.install()
    if app:
        app._solidflow_beta4_controller = _controller
    return _controller


def uninstall():
    global _controller
    if _controller:
        _controller.uninstall()
        _controller = None
