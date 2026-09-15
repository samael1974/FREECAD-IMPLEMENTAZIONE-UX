# -*- coding: utf-8 -*-
"""SolidFlow always-available display style bar positioned below the navigation cube."""

import FreeCAD as App
import FreeCADGui as Gui
from PySide import QtCore, QtWidgets

PREF_PATH = "User parameter:BaseApp/Preferences/Mod/SolidFlowUX"


def _prefs():
    return App.ParamGet(PREF_PATH)


def display_bar_enabled():
    return _prefs().GetBool("DisplayStyleBar", True)


def set_display_bar_enabled(enabled):
    _prefs().SetBool("DisplayStyleBar", bool(enabled))




def _home_view():
    """SolidFlow Home: Shift keeps orientation; normal click returns to axonometric and fits all."""
    try:
        view = Gui.ActiveDocument.ActiveView if Gui.ActiveDocument else None
    except Exception:
        view = None
    if view is None:
        return
    try:
        modifiers = QtWidgets.QApplication.keyboardModifiers()
    except Exception:
        modifiers = QtCore.Qt.NoModifier
    try:
        if not (modifiers & QtCore.Qt.ShiftModifier):
            view.viewAxonometric()
        view.fitAll()
    except Exception:
        try:
            Gui.runCommand("Std_ViewAxonometric")
            Gui.runCommand("Std_ViewFitAll")
        except Exception:
            pass


def _run_draw_style(index, fallback_name=None):
    """Run FreeCAD's native global draw-style command, with an ActiveView fallback."""
    try:
        Gui.runCommand("Std_DrawStyle", int(index))
        return True
    except Exception:
        pass
    if fallback_name:
        try:
            if Gui.ActiveDocument:
                Gui.ActiveDocument.ActiveView.setDrawStyle(fallback_name)
                return True
        except Exception:
            pass
    return False


def _material_editor():
    try:
        cmd = Gui.Command.get("Std_SetMaterial")
        if cmd:
            Gui.runCommand("Std_SetMaterial")
            return
    except Exception:
        pass
    try:
        QtWidgets.QMessageBox.information(
            Gui.getMainWindow(),
            "SolidFlow - Materiale",
            "Il comando Materiale non è disponibile nel contesto corrente. Seleziona prima un oggetto solido.",
        )
    except Exception:
        pass


def _render_view():
    # This is intentionally a viewport rendering preset, not a ray tracer.
    _run_draw_style(5, "Shaded")
    try:
        Gui.runCommand("Std_PerspectiveCamera")
    except Exception:
        pass


def _active_view_host(main_window):
    """Find the current MDI document widget so the bar overlays the 3D view."""
    try:
        mdi = main_window.findChild(QtWidgets.QMdiArea)
        if mdi:
            sub = mdi.activeSubWindow()
            if sub:
                return sub.widget() or sub
    except Exception:
        pass
    try:
        w = main_window.activeWindow()
        if isinstance(w, QtWidgets.QWidget):
            return w
    except Exception:
        pass
    return None


class DisplayStyleBar(QtWidgets.QFrame):
    """Compact viewport navigation/style palette kept just below FreeCAD's navigation cube."""

    def __init__(self, main_window):
        super().__init__(main_window)
        self.main_window = main_window
        self._host = None
        self.setObjectName("SolidFlowDisplayStyleBar")
        self.setStyleSheet("""
            QFrame#SolidFlowDisplayStyleBar {
                border: 1px solid palette(mid);
                border-radius: 7px;
                background: palette(window);
            }
            QToolButton {
                min-width: 62px;
                min-height: 29px;
                padding: 2px 5px;
                border-radius: 4px;
                font-size: 11px;
            }
            QToolButton:hover {
                background: palette(highlight);
                color: palette(highlighted-text);
            }
        """)
        grid = QtWidgets.QGridLayout(self)
        grid.setContentsMargins(4, 4, 4, 4)
        grid.setHorizontalSpacing(3)
        grid.setVerticalSpacing(3)

        specs = [
            ("🏠 Home", "Isometrica + Inquadra tutto. Shift+clic: solo Inquadra tutto", _home_view),
            ("Wire", "Wireframe", lambda: _run_draw_style(2, "Wireframe")),
            ("Solido", "Solido ombreggiato", lambda: _run_draw_style(5, "Shaded")),
            ("Bordi", "Solido con bordi / Flat Lines", lambda: _run_draw_style(6, "Flat Lines")),
            ("Nascoste", "Linee nascoste", lambda: _run_draw_style(3, "Hidden Line")),
            ("Render", "Vista ombreggiata prospettica (viewport, non ray tracing)", _render_view),
            ("Materiale", "Apri il materiale dell'oggetto selezionato", _material_editor),
        ]
        for i, (text, tip, callback) in enumerate(specs):
            b = QtWidgets.QToolButton(self)
            b.setText(text)
            b.setToolTip(tip)
            b.clicked.connect(lambda _checked=False, cb=callback: cb())
            grid.addWidget(b, i // 3, i % 3)
        self.adjustSize()
        self.hide()

    def set_enabled(self, enabled):
        set_display_bar_enabled(enabled)
        if not enabled:
            self.hide()
        else:
            self.sync_position()

    def sync_position(self):
        if not display_bar_enabled() or not Gui.ActiveDocument:
            self.hide()
            return
        host = _active_view_host(self.main_window)
        if host is None:
            self.hide()
            return
        if host is not self._host:
            self._host = host
            self.setParent(host)
            self.setWindowFlags(QtCore.Qt.Widget)
            self.show()
        self.adjustSize()
        # Navigation cube occupies the top-right corner. Keep a compact margin below it.
        x = max(4, host.width() - self.width() - 18)
        y = min(max(132, 8), max(8, host.height() - self.height() - 8))
        self.move(x, y)
        self.raise_()
        self.show()
