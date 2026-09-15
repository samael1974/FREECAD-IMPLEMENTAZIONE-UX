# -*- coding: utf-8 -*-
"""SolidFlow UX beta.9 stabilization layer.

Based on the first full user test pass.  It deliberately focuses on making the
already-developed functions visible and coherent before adding more features.
"""
from __future__ import annotations

import FreeCAD as App
import FreeCADGui as Gui
from PySide import QtCore, QtWidgets

VERSION = "0.4.0-beta.9"
ROOT = App.ParamGet("User parameter:BaseApp/Preferences/Mod/SolidFlowUX")


def _patch_constraint_specs():
    """Use beta.4's richer selection classifier directly inside the S palette."""
    try:
        import solidflow_ui as ui
        import solidflow_beta4 as b4
    except Exception as exc:
        App.Console.PrintWarning("SolidFlow beta.9 vincoli: %s\n" % exc)
        return
    if getattr(ui, "_solidflow_beta9_constraints", False):
        return
    fallback = ui._smart_constraint_specs

    def specs():
        try:
            sketch = b4._active_sketch()
            if sketch is None:
                return fallback()
            items = b4._selected_items(sketch)
            suggestions = b4._suggestions(items)
            if not suggestions:
                return fallback()
            out = []
            for label, command, tip, accent in suggestions:
                pretty = {
                    "Collin./Tang.": "Collineare / Tangente",
                    "Perpend.": "Perpendicolare",
                    "Orizz.": "Orizzontale",
                    "Vert.": "Verticale",
                }.get(label, label)
                out.append(ui.ActionSpec(pretty, command=command, tooltip=tip, emphasis=bool(accent)))
            return out
        except Exception as exc:
            App.Console.PrintWarning("SolidFlow beta.9 suggerimenti: %s\n" % exc)
            return fallback()

    ui._solidflow_beta9_original_constraint_specs = fallback
    ui._smart_constraint_specs = specs
    ui._solidflow_beta9_constraints = True


def _force_viewbar_once():
    """Migrate old installations that never received the beta.3 display bar."""
    try:
        import solidflow_ui as ui
        import solidflow_viewbar as vb
        vb.set_display_bar_enabled(True)
        controller = getattr(ui, "_controller", None)
        bar = getattr(controller, "viewbar", None)
        if bar is not None:
            bar.set_enabled(True)
            bar.sync_position()
        ROOT.SetBool("Beta9DisplayBarReady", True)
    except Exception as exc:
        App.Console.PrintWarning("SolidFlow beta.9 viewbar: %s\n" % exc)


def _reaugment_menus():
    """Ask every additive layer to repopulate menus after the new core menu exists."""
    for module_name, function_name in (
        ("solidflow_beta4", "_augment_menu"),
        ("solidflow_beta7", None),
        ("solidflow_patterns", "_augment_menu"),
    ):
        try:
            mod = __import__(module_name)
            if module_name == "solidflow_beta4":
                ctrl = getattr(mod, "_controller", None)
                fn = getattr(ctrl, "_augment_menu", None)
            elif module_name == "solidflow_beta7":
                ctrl = getattr(mod, "_controller", None)
                fn = getattr(ctrl, "_augment_menu", None)
            else:
                fn = getattr(mod, function_name, None)
            if callable(fn):
                fn()
        except Exception as exc:
            App.Console.PrintWarning("SolidFlow beta.9 menu %s: %s\n" % (module_name, exc))


def _status_text():
    status = dict(getattr(App, "__solidflow_status__", {}) or {})
    expected = (
        "solidflow_ui", "solidflow_beta4", "solidflow_beta5", "solidflow_beta6",
        "solidflow_beta7", "solidflow_patterns",
    )
    lines = ["SolidFlow beta.9 — verifica caricamento"]
    for name in expected:
        value = status.get(name, "NON REGISTRATO")
        lines.append("%s: %s" % (name, value))
    try:
        import solidflow_ui as ui
        lines.append("Core UI: %s" % getattr(ui, "VERSION", "?"))
        lines.append("Barra vista: %s" % getattr(getattr(ui, "_controller", None), "viewbar", None))
    except Exception as exc:
        lines.append("Core UI ERROR: %s" % exc)
    return "\n".join(lines)


def show_layer_status():
    text = _status_text()
    App.Console.PrintMessage(text + "\n")
    box = QtWidgets.QMessageBox(Gui.getMainWindow())
    box.setWindowTitle("SolidFlow — Stato moduli")
    box.setText("Controllo caricamento SolidFlow")
    box.setDetailedText(text)
    box.exec_()


def _add_status_action():
    try:
        for menu in Gui.getMainWindow().findChildren(QtWidgets.QMenu):
            if menu.title().replace("&", "").strip().lower() != "solidflow":
                continue
            if menu.findChild(QtCore.QObject, "SolidFlowBeta9StatusMarker"):
                return
            marker = QtCore.QObject(menu)
            marker.setObjectName("SolidFlowBeta9StatusMarker")
            menu.addSeparator()
            menu.addAction("Stato moduli / diagnostica beta.9…", show_layer_status)
            return
    except Exception as exc:
        App.Console.PrintWarning("SolidFlow beta.9 status menu: %s\n" % exc)


class StabilizationController:
    def __init__(self):
        self._installed = False

    def install(self):
        if self._installed:
            return self
        _patch_constraint_specs()
        _force_viewbar_once()
        self._installed = True
        QtCore.QTimer.singleShot(700, _force_viewbar_once)
        QtCore.QTimer.singleShot(900, _reaugment_menus)
        QtCore.QTimer.singleShot(1400, _reaugment_menus)
        QtCore.QTimer.singleShot(1500, _add_status_action)
        QtCore.QTimer.singleShot(2400, _add_status_action)
        App.Console.PrintMessage("SolidFlow UX %s: stabilization layer loaded.\n" % VERSION)
        return self


_controller = None


def install():
    global _controller
    if _controller is None:
        _controller = StabilizationController().install()
    return _controller
