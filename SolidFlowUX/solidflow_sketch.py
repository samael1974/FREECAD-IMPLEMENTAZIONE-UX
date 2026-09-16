# -*- coding: utf-8 -*-
"""SolidFlow consolidated Sketch UX controller — beta10.

Replaces the old beta.4 quick-constraint runtime layer.  Responsibilities:
- reversible SolidWorks-like viewport/sketch colour preset;
- one automatic mini-window with 3-5 likely native constraints/dimensions;
- explicit user confirmation for every constraint;
- shared Smart Sketch settings and snap tuning.

Pattern buttons live directly in ``solidflow_ui`` so they cannot disappear
because of a patch/load-order issue.
"""
from __future__ import annotations

import FreeCAD as App
import FreeCADGui as Gui
from PySide import QtCore, QtGui, QtWidgets

import solidflow_smart as smart

VERSION = "0.4.0-beta.10-sketch"
ROOT = App.ParamGet("User parameter:BaseApp/Preferences/Mod/SolidFlowUX")
VIEW = App.ParamGet("User parameter:BaseApp/Preferences/View")
THEME_BACKUP = App.ParamGet("User parameter:BaseApp/Preferences/Mod/SolidFlowUX/ThemeBackup")


def _rgba(r, g, b, a=255):
    return ((r & 255) << 24) | ((g & 255) << 16) | ((b & 255) << 8) | (a & 255)


_THEME_BOOL = {
    "Gradient": True,
    "RadialGradient": False,
    "Simple": False,
    "UseBackgroundColorMid": False,
}

# SolidWorks-like working palette.  These are intentionally a reproducible
# SolidFlow preset, not a claim that every SolidWorks installation uses fixed
# RGB values (SolidWorks colour schemes/scenes are user-configurable).
_THEME_UINT = {
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
    # Sketch status convention: blue under-defined, dark fully-defined,
    # external/reference purple, invalid red.
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


def _backup_theme_once():
    if THEME_BACKUP.GetBool("Stored", False):
        return
    for key in _THEME_BOOL:
        THEME_BACKUP.SetBool("b_" + key, VIEW.GetBool(key, False))
    for key in _THEME_UINT:
        THEME_BACKUP.SetUnsigned("u_" + key, VIEW.GetUnsigned(key, 0))
    THEME_BACKUP.SetBool("Stored", True)


def apply_sw_like_theme():
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


def restore_previous_theme():
    if not THEME_BACKUP.GetBool("Stored", False):
        return
    for key in _THEME_BOOL:
        VIEW.SetBool(key, THEME_BACKUP.GetBool("b_" + key, False))
    for key in _THEME_UINT:
        VIEW.SetUnsigned(key, THEME_BACKUP.GetUnsigned("u_" + key, 0))
    ROOT.SetBool("SWLikeTheme", False)
    try:
        Gui.updateGui()
    except Exception:
        pass


def _command_action(command):
    try:
        native = Gui.Command.get(command)
        actions = native.getAction() if native else []
        return actions[0] if actions else None
    except Exception:
        return None


def _run_native(command):
    try:
        Gui.runCommand(command, 0)
        Gui.updateGui()
    except Exception as exc:
        App.Console.PrintError("SolidFlow Sketch command %s: %s\n" % (command, exc))


class SketchHintBar(QtWidgets.QFrame):
    """Small confirmation bar shown automatically after Sketch selection."""

    def __init__(self, controller):
        super().__init__(Gui.getMainWindow(), QtCore.Qt.Tool | QtCore.Qt.FramelessWindowHint)
        self.controller = controller
        self.setObjectName("SolidFlowSketchHintBar")
        self.setAttribute(QtCore.Qt.WA_ShowWithoutActivating, True)
        self.setFocusPolicy(QtCore.Qt.NoFocus)
        self.setStyleSheet(
            "QFrame#SolidFlowSketchHintBar {background:rgba(248,249,251,248);"
            "border:1px solid #8193a2;border-radius:7px;}"
            "QToolButton{min-height:31px;padding:3px 8px;border:0;border-radius:4px;"
            "font-size:11px;color:#20262b;}"
            "QToolButton:hover{background:#dce9f3;}"
            "QToolButton[dimension='true']{font-weight:600;}"
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

    def rebuild(self, suggestions):
        self._clear()
        for suggestion in suggestions[:5]:
            button = QtWidgets.QToolButton(self)
            button.setText(suggestion["label"])
            button.setToolTip(suggestion["reason"] + " — clic per confermare")
            button.setFocusPolicy(QtCore.Qt.NoFocus)
            button.setProperty("dimension", "true" if suggestion.get("kind") == "dimension" else "false")
            action = _command_action(suggestion["command"])
            if action:
                try:
                    button.setIcon(action.icon())
                    button.setIconSize(QtCore.QSize(18, 18))
                except Exception:
                    pass
            button.clicked.connect(
                lambda _checked=False, cmd=suggestion["command"]: self.controller.run_command(cmd)
            )
            self.layout.addWidget(button)

        more = QtWidgets.QToolButton(self)
        more.setText("Altri…")
        more.setToolTip("Mostra tutti i vincoli e le quote native disponibili")
        more.setFocusPolicy(QtCore.Qt.NoFocus)
        more.clicked.connect(self.controller.show_more)
        self.layout.addWidget(more)
        self.adjustSize()

    def show_near_cursor(self):
        self.adjustSize()
        cursor = QtGui.QCursor.pos()
        pos = cursor + QtCore.QPoint(22, 24)
        screen = QtWidgets.QApplication.screenAt(cursor) or QtWidgets.QApplication.primaryScreen()
        if screen:
            area = screen.availableGeometry()
            pos.setX(max(area.left() + 8, min(pos.x(), area.right() - self.width() - 8)))
            pos.setY(max(area.top() + 8, min(pos.y(), area.bottom() - self.height() - 8)))
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


class SketchUXController(QtCore.QObject):
    def __init__(self):
        super().__init__(Gui.getMainWindow())
        self.bar = SketchHintBar(self)
        self.observer = _SelectionObserver(self)
        self.timer = QtCore.QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.setInterval(80)
        self.timer.timeout.connect(self.update)
        self._installed = False

    def install(self):
        if self._installed:
            return self
        Gui.Selection.addObserver(self.observer)
        self._installed = True
        smart.apply_smart_snap_preferences()
        if ROOT.GetBool("SWLikeTheme", True):
            apply_sw_like_theme()
        QtCore.QTimer.singleShot(700, self._augment_menu)
        QtCore.QTimer.singleShot(1500, self._augment_menu)
        App.Console.PrintMessage("SolidFlow %s: Smart Sketch consolidato attivo.\n" % VERSION)
        return self

    def schedule_update(self):
        if self._installed:
            self.timer.start()

    def update(self):
        if not smart.constraint_hints_enabled() or smart.active_sketch() is None:
            self.bar.hide()
            return
        suggestions = smart.constraint_suggestions(limit=5)
        if not suggestions:
            self.bar.hide()
            return
        self.bar.rebuild(suggestions)
        self.bar.show_near_cursor()

    def run_command(self, command):
        self.bar.hide()
        _run_native(command)
        QtCore.QTimer.singleShot(120, self.schedule_update)

    def show_more(self):
        menu = QtWidgets.QMenu(self.bar)
        for label, command in smart.all_constraint_actions():
            action = menu.addAction(label)
            native = _command_action(command)
            if native:
                try:
                    action.setIcon(native.icon())
                except Exception:
                    pass
            action.triggered.connect(lambda _checked=False, cmd=command: self.run_command(cmd))
        menu.exec_(QtGui.QCursor.pos())

    def _augment_menu(self):
        try:
            target = None
            for menu in Gui.getMainWindow().findChildren(QtWidgets.QMenu):
                if menu.title().replace("&", "").strip().lower() == "solidflow":
                    target = menu
                    break
            if target is None or target.findChild(QtCore.QObject, "SolidFlowSketchCoreMarker"):
                return
            marker = QtCore.QObject(target)
            marker.setObjectName("SolidFlowSketchCoreMarker")
            target.addSeparator()
            submenu = target.addMenu("Sketch intelligente")
            settings = submenu.addAction("Impostazioni Smart Sketch…")
            settings.triggered.connect(smart.show_smart_sketch_settings)
            theme = submenu.addAction("Tema SolidWorks-like")
            theme.setCheckable(True)
            theme.setChecked(ROOT.GetBool("SWLikeTheme", True))
            theme.toggled.connect(lambda state: apply_sw_like_theme() if state else restore_previous_theme())
            restore = submenu.addAction("Ripristina colori precedenti")
            restore.triggered.connect(restore_previous_theme)
        except Exception as exc:
            App.Console.PrintWarning("SolidFlow Sketch menu: %s\n" % exc)

    def uninstall(self):
        if not self._installed:
            return
        try:
            Gui.Selection.removeObserver(self.observer)
        except Exception:
            pass
        self.timer.stop()
        self.bar.hide()
        self._installed = False


_controller = None


def install():
    global _controller
    if _controller is None:
        _controller = SketchUXController().install()
    return _controller


def uninstall():
    global _controller
    if _controller:
        _controller.uninstall()
        _controller = None
