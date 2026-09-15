# -*- coding: utf-8 -*-
"""GUI bootstrap for SolidFlow UX.

Drop-in replacement for InitGui.py in the SolidFlowUX add-on folder.
It keeps the existing beta.3 UI module and loads the beta.4 Smart Sketch layer.
"""

import FreeCAD as App
import FreeCADGui as Gui


def _ui_module():
    try:
        import solidflow_ui
        return solidflow_ui
    except Exception as exc:
        App.Console.PrintError("SolidFlow: impossibile importare solidflow_ui: %s\n" % exc)
        return None


def _ensure_ui_installed():
    module = _ui_module()
    if module is not None:
        try:
            install = getattr(module, "install", None)
            if callable(install):
                install()
        except Exception as exc:
            App.Console.PrintError("SolidFlow UI install: %s\n" % exc)
    return module


def _show_palette():
    module = _ensure_ui_installed()
    if module is None:
        return
    try:
        show = getattr(module, "show_palette", None)
        if callable(show):
            show()
            return
    except Exception:
        pass
    try:
        controller = getattr(module, "_controller", None)
        palette = getattr(controller, "palette", None)
        if palette is not None:
            palette.show_near_cursor()
            return
    except Exception as exc:
        App.Console.PrintError("SolidFlow palette: %s\n" % exc)


class _ShowShortcutBar:
    def GetResources(self):
        return {
            "MenuText": "Mostra palette SolidFlow",
            "ToolTip": "Apre la palette contestuale SolidFlow vicino al cursore",
            "Accel": "S",
        }

    def IsActive(self):
        return True

    def Activated(self):
        _show_palette()


class _ToggleShortcut:
    def GetResources(self):
        return {
            "MenuText": "Usa tasto S",
            "ToolTip": "Attiva/disattiva il richiamo rapido SolidFlow con il tasto S",
        }

    def IsActive(self):
        return True

    def Activated(self):
        module = _ensure_ui_installed()
        if module is None:
            return
        # Prefer the native beta.3 implementation if it exposes one.
        for name in ("toggle_shortcut", "toggle_s_shortcut", "toggle_shortcut_enabled"):
            fn = getattr(module, name, None)
            if callable(fn):
                try:
                    fn()
                    return
                except Exception:
                    pass
        # Fallback: common controller/parameter conventions used by SolidFlow.
        try:
            controller = getattr(module, "_controller", None)
            if controller is not None and hasattr(controller, "enabled"):
                controller.enabled = not bool(controller.enabled)
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

# Existing beta.3 layer: palette S, PartDesign helpers, import assistant,
# navigation/display toolbar and Home command.
_ensure_ui_installed()

# beta.4 layer: quick constraints, smart snap tuning and SW-like visual preset.
try:
    import solidflow_beta4
    solidflow_beta4.install()
except Exception as exc:
    App.Console.PrintError("SolidFlow beta.4 install: %s\n" % exc)
