# -*- coding: utf-8 -*-
"""SolidFlow UX GUI bootstrap — beta12 UX stabilization.

The plain ``S`` key is intentionally owned only by ``solidflow_ui``.

Load order:
1. consolidated UI/palette/event-filter;
2. consolidated Smart Sketch / dimensions / quick constraints / theme;
3. beta.5 Revolution+ / Studio Shadows;
4. beta.6 native Sweep / Loft / Helix / Thread Wizard;
5. beta.7 Mesh Doctor / Appearance Studio integration;
6. beta11 profile-region picker, interactive Fillet and 3D path workflows;
7. beta12 UX stabilization (direct regions, external refs, dimensions, shadows).

Historical beta.4/patterns/beta.9 files remain in the repository for migration
and comparison but are no longer runtime patch layers.
"""

import traceback

import FreeCAD as App
import FreeCADGui as Gui

STATUS = {}
App.__solidflow_status__ = STATUS


def _record(name, module=None, error=None):
    if error is None:
        version = getattr(module, "VERSION", "base") if module is not None else "?"
        STATUS[name] = "OK " + str(version)
    else:
        STATUS[name] = "ERRORE: " + str(error)


def _load_layer(name, required=False):
    try:
        module = __import__(name)
        installer = getattr(module, "install", None)
        if callable(installer):
            installer()
        _record(name, module)
        return module
    except ModuleNotFoundError as exc:
        STATUS[name] = "assente"
        message = "SolidFlow: layer %s assente: %s\n" % (name, exc)
        if required:
            App.Console.PrintError(message)
        else:
            App.Console.PrintWarning(message)
    except Exception as exc:
        _record(name, error=exc)
        App.Console.PrintError("SolidFlow %s:\n%s\n" % (name, traceback.format_exc()))
    return None


_BASE_UI = _load_layer("solidflow_ui", required=True)


class _ShowShortcutBar:
    def GetResources(self):
        return {
            "MenuText": "Mostra palette SolidFlow",
            "ToolTip": "Apre la palette contestuale SolidFlow vicino al cursore",
        }

    def IsActive(self):
        return _BASE_UI is not None

    def Activated(self):
        if _BASE_UI is None:
            return
        try:
            controller = getattr(_BASE_UI, "_controller", None)
            palette = getattr(controller, "palette", None)
            if palette is not None:
                palette.show_near_cursor()
        except Exception as exc:
            App.Console.PrintError("SolidFlow palette: %s\n" % exc)


class _ToggleShortcut:
    def GetResources(self):
        return {
            "MenuText": "Usa tasto S",
            "ToolTip": "Attiva/disattiva il richiamo rapido SolidFlow con il tasto S",
        }

    def IsActive(self):
        return _BASE_UI is not None

    def Activated(self):
        if _BASE_UI is None:
            return
        for name in ("toggle_shortcut", "toggle_s_shortcut", "toggle_shortcut_enabled"):
            fn = getattr(_BASE_UI, name, None)
            if callable(fn):
                try:
                    fn()
                    return
                except Exception:
                    pass


try:
    Gui.addCommand("SolidFlow_ShowShortcutBar", _ShowShortcutBar())
    Gui.addCommand("SolidFlow_ToggleShortcut", _ToggleShortcut())
except Exception as exc:
    App.Console.PrintWarning("SolidFlow: registrazione comandi GUI: %s\n" % exc)


try:
    from PySide import QtGui, QtWidgets
    if not hasattr(QtWidgets, "QActionGroup") and hasattr(QtGui, "QActionGroup"):
        QtWidgets.QActionGroup = QtGui.QActionGroup
except Exception:
    pass

_load_layer("solidflow_sketch", required=True)
_load_layer("solidflow_beta5")
_load_layer("solidflow_beta6")
_load_layer("solidflow_beta7")
_load_layer("solidflow_profiles", required=True)
_load_layer("solidflow_workflows", required=True)
_load_layer("solidflow_beta12", required=True)

App.Console.PrintMessage(
    "SolidFlow beta12 bootstrap: %s\nLayer: %s\n" % (__file__, STATUS)
)
