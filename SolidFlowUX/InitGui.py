# -*- coding: utf-8 -*-
"""SolidFlow UX GUI bootstrap.

The plain ``S`` key is intentionally owned only by ``solidflow_ui``'s event
filter. Do not add a second QAction/FreeCAD accelerator for ``S`` here.

Load order:
1. stable base UI/palette/event-filter;
2. beta.4 Smart Sketch / Quick Constraints;
3. beta.5 Fillet Doctor / Revolution+ / Studio Shadows;
4. beta.6 Sweep / Loft / Helix / Thread Wizard;
5. beta.7 Mesh Doctor / Appearance Studio / palette integration;
6. beta.8 pattern integration: Sketch X/Y + polar, PartDesign 3D patterns.

Every newer layer is additive: a failure in an experimental layer must not
prevent the stable ``S`` palette from loading.
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


def _load_base_ui():
    try:
        import solidflow_ui
        installer = getattr(solidflow_ui, "install", None)
        if callable(installer):
            installer()
        _record("solidflow_ui", solidflow_ui)
        return solidflow_ui
    except Exception as exc:
        _record("solidflow_ui", error=exc)
        App.Console.PrintError(
            "SolidFlow: errore caricamento interfaccia base:\n%s\n" % traceback.format_exc()
        )
        return None


def _load_layer(name):
    try:
        module = __import__(name)
        installer = getattr(module, "install", None)
        if callable(installer):
            installer()
        _record(name, module)
        return module
    except ModuleNotFoundError as exc:
        STATUS[name] = "assente"
        App.Console.PrintWarning("SolidFlow: layer %s assente: %s\n" % (name, exc))
    except Exception as exc:
        _record(name, error=exc)
        App.Console.PrintError(
            "SolidFlow %s:\n%s\n" % (name, traceback.format_exc())
        )
    return None


_BASE_UI = _load_base_ui()


class _ShowShortcutBar:
    """Menu/toolbar command only. No keyboard accelerator on purpose."""

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
        params = App.ParamGet("User parameter:BaseApp/Preferences/Mod/SolidFlowUX")
        current = params.GetBool("UseSShortcut", True)
        params.SetBool("UseSShortcut", not current)
        App.Console.PrintMessage(
            "SolidFlow: tasto S %s.\n" % ("attivo" if not current else "disattivato")
        )


try:
    Gui.addCommand("SolidFlow_ShowShortcutBar", _ShowShortcutBar())
    Gui.addCommand("SolidFlow_ToggleShortcut", _ToggleShortcut())
except Exception as exc:
    App.Console.PrintWarning("SolidFlow: registrazione comandi GUI: %s\n" % exc)


_load_layer("solidflow_beta4")

# Qt6/PySide6 moved QActionGroup from QtWidgets to QtGui. FreeCAD's PySide
# compatibility shim varies by build, so provide the legacy location expected
# by the beta.5 UI when necessary.
try:
    from PySide import QtGui, QtWidgets
    if not hasattr(QtWidgets, "QActionGroup") and hasattr(QtGui, "QActionGroup"):
        QtWidgets.QActionGroup = QtGui.QActionGroup
except Exception:
    pass

_load_layer("solidflow_beta5")
_load_layer("solidflow_beta6")
_load_layer("solidflow_beta7")
_load_layer("solidflow_patterns")

App.Console.PrintMessage(
    "SolidFlow bootstrap: %s\nLayer: %s\n" % (__file__, STATUS)
)
