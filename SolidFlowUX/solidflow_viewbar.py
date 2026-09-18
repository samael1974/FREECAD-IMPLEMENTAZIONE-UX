# -*- coding: utf-8 -*-
"""SolidFlow always-available vertical display/style bar below the navigation cube."""

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


def _studio_controller():
    try:
        import solidflow_beta5
        return solidflow_beta5._studio
    except Exception:
        return None


def _toggle_shadows():
    studio = _studio_controller()
    if studio is not None:
        try:
            studio.toggle()
            return
        except Exception as exc:
            App.Console.PrintWarning("SolidFlow Ombre/Piano: %s\n" % exc)
    try:
        QtWidgets.QMessageBox.information(
            Gui.getMainWindow(), "SolidFlow - Ombre/Piano",
            "Il modulo Studio non è disponibile. Controlla SolidFlow > Diagnostica SolidFlow.",
        )
    except Exception:
        pass


def _set_studio_plane(plane):
    studio = _studio_controller()
    if studio is None:
        return
    try:
        studio.set_plane(str(plane))
        if not getattr(studio, "enabled", False):
            studio.set_enabled(True)
    except Exception as exc:
        App.Console.PrintWarning("SolidFlow piano %s: %s\n" % (plane, exc))


def _material_editor():
    try:
        import solidflow_appearance
        solidflow_appearance.launch_appearance_studio()
        return
    except Exception as exc:
        App.Console.PrintWarning("SolidFlow Materiale: %s\n" % exc)
    try:
        cmd = Gui.Command.get("Std_SetMaterial")
        if cmd:
            Gui.runCommand("Std_SetMaterial")
            return
    except Exception:
        pass
    QtWidgets.QMessageBox.information(
        Gui.getMainWindow(),
        "SolidFlow - Materiale",
        "Seleziona prima un oggetto solido, poi riprova.",
    )


def _studio_view():
    """Fast modelling/material preview, deliberately not a ray-traced renderer."""
    _run_draw_style(5, "Shaded")
    try:
        Gui.runCommand("Std_PerspectiveCamera")
    except Exception:
        pass
    try:
        if Gui.ActiveDocument:
            Gui.ActiveDocument.ActiveView.fitAll()
    except Exception:
        pass


def _active_view_host(main_window):
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
    """Vertical modelling/view palette kept below FreeCAD's navigation cube."""

    def __init__(self, main_window):
        super().__init__(main_window)
        self.main_window = main_window
        self._host = None
        self._watched = []
        self._mdi = None
        self._sync_timer = QtCore.QTimer(self)
        self._sync_timer.setSingleShot(True)
        self._sync_timer.timeout.connect(self.sync_position)
        self.setObjectName("SolidFlowDisplayStyleBar")
        self.setStyleSheet("""
            QFrame#SolidFlowDisplayStyleBar {
                border: 1px solid palette(mid);
                border-radius: 7px;
                background: palette(window);
            }
            QToolButton {
                min-width: 92px;
                min-height: 28px;
                padding: 3px 7px;
                border-radius: 4px;
                font-size: 11px;
                text-align: left;
            }
            QToolButton:hover {
                background: palette(highlight);
                color: palette(highlighted-text);
            }
        """)
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(3)

        specs = [
            ("🏠  Home", "Isometrica + Inquadra tutto. Shift+clic: solo Inquadra tutto", _home_view),
            ("Wire", "Wireframe", lambda: _run_draw_style(2, "Wireframe")),
            ("Solido", "Solido ombreggiato", lambda: _run_draw_style(5, "Shaded")),
            ("Bordi", "Solido con bordi / Flat Lines", lambda: _run_draw_style(6, "Flat Lines")),
            ("Nascoste", "Linee nascoste", lambda: _run_draw_style(3, "Hidden Line")),
        ]
        for text, tip, callback in specs:
            b = QtWidgets.QToolButton(self)
            b.setText(text)
            b.setToolTip(tip)
            b.clicked.connect(lambda _checked=False, cb=callback: cb())
            layout.addWidget(b)

        shadow = QtWidgets.QToolButton(self)
        shadow.setText("Ombre/Piano")
        shadow.setToolTip("Attiva piano di appoggio e ombra; usa la freccia per scegliere XY/XZ/YZ")
        shadow.clicked.connect(_toggle_shadows)
        menu = QtWidgets.QMenu(shadow)
        menu.addAction("Piano XY", lambda: _set_studio_plane("XY"))
        menu.addAction("Piano XZ", lambda: _set_studio_plane("XZ"))
        menu.addAction("Piano YZ", lambda: _set_studio_plane("YZ"))
        shadow.setMenu(menu)
        try:
            shadow.setPopupMode(QtWidgets.QToolButton.MenuButtonPopup)
        except Exception:
            pass
        layout.addWidget(shadow)

        studio = QtWidgets.QToolButton(self)
        studio.setText("Studio")
        studio.setToolTip("Vista rapida materiali/modello: shaded + prospettiva. Non è un ray tracer.")
        studio.clicked.connect(_studio_view)
        layout.addWidget(studio)

        material = QtWidgets.QToolButton(self)
        material.setText("Materiale")
        material.setToolTip("Appearance Studio: colore, materiale e texture")
        material.clicked.connect(_material_editor)
        layout.addWidget(material)

        self.adjustSize()
        self.hide()
        self._watch_views()

    def _schedule_sync(self, *_args):
        if not self._sync_timer.isActive():
            self._sync_timer.start(0)

    def _watch_views(self):
        mdi = self.main_window.findChild(QtWidgets.QMdiArea)
        if mdi is not self._mdi:
            if self._mdi is not None:
                try:
                    self._mdi.subWindowActivated.disconnect(self._schedule_sync)
                except RuntimeError:
                    pass
            self._mdi = mdi
            if mdi is not None:
                mdi.subWindowActivated.connect(self._schedule_sync)
        sub = mdi.activeSubWindow() if mdi else None
        watched = [self.main_window, mdi, sub, sub.widget() if sub else None]
        watched = [obj for obj in watched if obj is not None]
        for obj in self._watched:
            if obj not in watched:
                try:
                    obj.removeEventFilter(self)
                except RuntimeError:
                    pass  # The previous document's widget was already deleted.
        for obj in watched:
            if obj not in self._watched:
                obj.installEventFilter(self)
        self._watched = watched

    def eventFilter(self, watched, event):
        if event.type() in (
            QtCore.QEvent.Resize, QtCore.QEvent.Move, QtCore.QEvent.Show,
            QtCore.QEvent.Hide, QtCore.QEvent.WindowActivate,
            QtCore.QEvent.WindowStateChange, QtCore.QEvent.ChildAdded,
            QtCore.QEvent.ChildRemoved, QtCore.QEvent.LayoutRequest,
        ):
            self._schedule_sync()
        return False

    def set_enabled(self, enabled):
        set_display_bar_enabled(enabled)
        if not enabled:
            self.hide()
        else:
            self.sync_position()

    def sync_position(self):
        self._watch_views()
        if not display_bar_enabled() or not Gui.ActiveDocument:
            self.hide()
            return
        host = _active_view_host(self.main_window)
        if host is None:
            self.hide()
            return
        # Keep ownership with the main window. Closing a document must never
        # delete the bar along with that document's MDI widget.
        self._host = host
        self.adjustSize()
        x = max(4, host.width() - self.width() - 18)
        # Below the navigation cube, with enough room for the vertical stack.
        y = min(max(132, 8), max(8, host.height() - self.height() - 8))
        self.move(host.mapTo(self.main_window, QtCore.QPoint(x, y)))
        self.raise_()
        self.show()
