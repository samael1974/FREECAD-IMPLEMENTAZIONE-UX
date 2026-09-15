# -*- coding: utf-8 -*-
"""SolidFlow UX GUI bootstrap.

IMPORTANT
---------
The plain ``S`` key is intentionally owned only by ``solidflow_ui``'s event
filter. Do not add a second Qt QAction/FreeCAD accelerator for ``S`` here:
having two independent shortcut mechanisms can prevent the contextual palette
from receiving the key event.

Load order:
1. proven beta.3 base UI/palette/event-filter;
2. beta.4 Smart Sketch / Quick Constraints;
3. beta.5 Fillet Doctor / Revolution+ / Studio Shadows.

Every newer layer is additive: a failure in an experimental layer must not
prevent the stable ``S`` palette from loading.
"""

import FreeCAD as App
import FreeCADGui as Gui


def _load_base_ui():
    """Install the stable SolidFlow palette/event-filter layer first."""
    try:
        import solidflow_ui
        installer = getattr(solidflow_ui, "install", None)
        if callable(installer):
            installer()
        return solidflow_ui
    except Exception as exc:
        App.Console.PrintError(
            "SolidFlow: errore caricamento interfaccia base: %s\n" % exc
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
                return
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


try:
    import solidflow_beta4
    solidflow_beta4.install()
except Exception as exc:
    App.Console.PrintError("SolidFlow beta.4 install: %s\n" % exc)


try:
    import solidflow_beta5
    solidflow_beta5.install()
except Exception as exc:
    App.Console.PrintError("SolidFlow beta.5 install: %s\n" % exc)
