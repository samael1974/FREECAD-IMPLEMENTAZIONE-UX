# -*- coding: utf-8 -*-
"""SolidFlow UX consolidated GUI core — beta.9 stabilization.

This replaces the historical base UI while preserving the public hooks used by
beta.4-beta.8.  The plain S key is owned only by this module.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Optional

import FreeCAD as App
import FreeCADGui as Gui
from PySide import QtCore, QtGui, QtWidgets

from solidflow_features import (
    create_sketch_on_face, add_support_face_references_to_active_sketch,
    auto_face_references_enabled, set_auto_face_references_enabled,
    launch_pad, launch_pocket, launch_revolution, launch_sweep,
    launch_edit_selected_feature, show_closed_profiles,
    selected_editable_feature, selected_face, selected_profile,
    selected_sketch_objects, selection_snapshot,
)
from solidflow_import import show_import_assistant
from solidflow_viewbar import DisplayStyleBar, display_bar_enabled, set_display_bar_enabled
from solidflow_smart import (
    apply_smart_snap_preferences, constraint_suggestions,
    set_smart_snap_enabled, show_smart_sketch_settings, smart_snap_enabled,
)

VERSION = "0.4.0-beta.9-core"
PREF_PATH = "User parameter:BaseApp/Preferences/Mod/SolidFlowUX"
_controller = None
_menu = None


@dataclass(frozen=True)
class ActionSpec:
    label: str
    command: Optional[str] = None
    callback: Optional[Callable] = None
    tooltip: str = ""
    icon_command: Optional[str] = None
    emphasis: bool = False


def _prefs(): return App.ParamGet(PREF_PATH)
def shortcut_enabled(): return _prefs().GetBool("EnableSShortcut", True)
def set_shortcut_enabled(v): _prefs().SetBool("EnableSShortcut", bool(v)); _controller and _controller.sync_menu_state()
def toggle_shortcut_enabled(): set_shortcut_enabled(not shortcut_enabled())
def toggle_shortcut(): toggle_shortcut_enabled()
def toggle_s_shortcut(): toggle_shortcut_enabled()
def auto_mini_toolbar_enabled(): return _prefs().GetBool("AutoMiniToolbar", True)
def set_auto_mini_toolbar_enabled(v): _prefs().SetBool("AutoMiniToolbar", bool(v)); _controller and _controller.sync_menu_state()
def mouse_gestures_enabled(): return False
def set_mouse_gestures_enabled(_v): return None


def _active_view():
    try: return Gui.ActiveDocument.ActiveView if Gui.ActiveDocument else None
    except Exception: return None
def _view_fit():
    v=_active_view(); v and v.fitAll()
def _view_axo():
    v=_active_view()
    if v: v.viewAxonometric(); v.fitAll()
def _view_front():
    v=_active_view()
    if v: v.viewFront(); v.fitAll()
def _view_top():
    v=_active_view()
    if v: v.viewTop(); v.fitAll()
def _view_right():
    v=_active_view()
    if v: v.viewRight(); v.fitAll()


def _command_object(name):
    try: return Gui.Command.get(name) if name else None
    except Exception: return None
def _command_action(name):
    try:
        cmd=_command_object(name); acts=cmd.getAction() if cmd else []
        return acts[0] if acts else None
    except Exception: return None
def _run_spec(spec):
    try:
        if spec.callback: spec.callback()
        elif spec.command: Gui.runCommand(spec.command, 0)
    except Exception as exc:
        App.Console.PrintError("SolidFlow command %s: %s\n" % (spec.label, exc))


def _is_sketch_edit_mode():
    try:
        edit=Gui.ActiveDocument.getInEdit() if Gui.ActiveDocument else None
        return bool(edit and edit.isDerivedFrom("SketcherGui::ViewProviderSketch"))
    except Exception: return False
def _workbench_name():
    try:
        wb=Gui.activeWorkbench(); return wb.name() if wb else ""
    except Exception: return ""


def _selection_kind():
    if selected_face(): return "Face"
    sketch, subs=selected_profile()
    if sketch and not _is_sketch_edit_mode(): return "SketchEdges" if subs else "Sketch"
    sketches=selected_sketch_objects()
    if len(sketches)==2: return "TwoSketches"
    sel=selection_snapshot()
    if not sel: return "None"
    names=[]
    for item in sel: names += list(getattr(item,"SubElementNames",[]) or [])
    if any(str(n).startswith("Edge") for n in names): return "Edge"
    if selected_editable_feature(): return "Feature"
    return "Object"


def current_context():
    if _is_sketch_edit_mode(): return "Sketch"
    kind=_selection_kind()
    if kind in ("Face","Sketch","SketchEdges","TwoSketches","Edge","Feature"): return "PartDesign"
    wb=_workbench_name(); return "PartDesign" if "PartDesign" in wb else "General"


def _launch_rev_best():
    try:
        import solidflow_beta5
        solidflow_beta5.launch_revolution_plus(); return
    except Exception: launch_revolution()
def _fillet_best():
    try:
        import solidflow_beta5
        solidflow_beta5.launch_fillet_doctor(); return
    except Exception:
        try: Gui.runCommand("PartDesign_Fillet",0)
        except Exception: pass


def _smart_constraint_specs():
    specs=[]
    try:
        for s in constraint_suggestions(limit=4):
            specs.append(ActionSpec(s["label"], command=s["command"], tooltip=s["reason"], emphasis=True))
    except Exception: pass
    return specs


def _sketch_groups():
    stable=[
        ActionSpec("Linea","Sketcher_CreateLine"), ActionSpec("Rettangolo","Sketcher_CreateRectangle"),
        ActionSpec("Cerchio","Sketcher_CreateCircle"), ActionSpec("Polilinea","Sketcher_CreatePolyline"),
    ]
    smart=_smart_constraint_specs()
    smart += [
        ActionSpec("Estrusione",callback=launch_pad,icon_command="PartDesign_Pad",tooltip="Chiude lo Sketch e apre la preview Pad"),
        ActionSpec("Taglio",callback=launch_pocket,icon_command="PartDesign_Pocket",tooltip="Chiude lo Sketch e apre la preview Pocket"),
        ActionSpec("Rivoluzione+",callback=_launch_rev_best,icon_command="PartDesign_Revolution"),
        ActionSpec("Proietta","Sketcher_CompExternal",tooltip="Geometria esterna"),
        ActionSpec("Riferimenti faccia",callback=add_support_face_references_to_active_sketch),
        ActionSpec("Chiudi Sketch","Sketcher_LeaveSketch"),
    ]
    return "DISEGNA",stable,"VINCOLI / FEATURE",smart


def _partdesign_groups():
    kind=_selection_kind()
    stable=[ActionSpec("Nuovo Sketch","PartDesign_NewSketch"),ActionSpec("Importa",callback=show_import_assistant),ActionSpec("Isometrica",callback=_view_axo),ActionSpec("Adatta",callback=_view_fit)]
    if kind=="Face":
        smart=[ActionSpec("Schizzo su faccia",callback=create_sketch_on_face,icon_command="PartDesign_NewSketch",emphasis=True),ActionSpec("Fillet Doctor",callback=_fillet_best,icon_command="PartDesign_Fillet"),ActionSpec("Chamfer","PartDesign_Chamfer"),ActionSpec("Hole","PartDesign_Hole")]
    elif kind in ("Sketch","SketchEdges"):
        smart=[ActionSpec("Profili chiusi",callback=show_closed_profiles,emphasis=True),ActionSpec("Estrusione",callback=launch_pad,icon_command="PartDesign_Pad"),ActionSpec("Taglio",callback=launch_pocket,icon_command="PartDesign_Pocket"),ActionSpec("Rivoluzione+",callback=_launch_rev_best,icon_command="PartDesign_Revolution")]
    elif kind=="TwoSketches":
        smart=[ActionSpec("Sweep",callback=launch_sweep,emphasis=True),ActionSpec("Loft",callback=lambda: _run_beta6("_launch_loft",False))]
    elif kind=="Edge": smart=[ActionSpec("Fillet Doctor",callback=_fillet_best,icon_command="PartDesign_Fillet"),ActionSpec("Chamfer","PartDesign_Chamfer")]
    elif kind=="Feature": smart=[ActionSpec("Modifica rapida",callback=launch_edit_selected_feature,emphasis=True),ActionSpec("Fillet Doctor",callback=_fillet_best,icon_command="PartDesign_Fillet"),ActionSpec("Chamfer","PartDesign_Chamfer")]
    else: smart=[ActionSpec("Estrusione",callback=launch_pad,icon_command="PartDesign_Pad"),ActionSpec("Taglio",callback=launch_pocket,icon_command="PartDesign_Pocket"),ActionSpec("Rivoluzione+",callback=_launch_rev_best,icon_command="PartDesign_Revolution")]
    return "PRINCIPALI",stable,"PER LA SELEZIONE",smart


def _run_beta6(name,*args):
    try:
        import solidflow_beta6; getattr(solidflow_beta6,name)(*args)
    except Exception as exc: App.Console.PrintError("SolidFlow beta6 %s: %s\n"%(name,exc))
def _general_groups():
    return "PRINCIPALI",[ActionSpec("Importa",callback=show_import_assistant),ActionSpec("Adatta",callback=_view_fit),ActionSpec("Isometrica",callback=_view_axo)],"VISTA",[ActionSpec("Frontale",callback=_view_front),ActionSpec("Alto",callback=_view_top),ActionSpec("Destra",callback=_view_right)]
def _groups_for_context(ctx): return _sketch_groups() if ctx=="Sketch" else (_partdesign_groups() if ctx=="PartDesign" else _general_groups())


def _is_text_entry_widget(widget):
    """Protect all text/numeric editors from the plain-S palette shortcut."""
    editable=(QtWidgets.QLineEdit,QtWidgets.QTextEdit,QtWidgets.QPlainTextEdit,QtWidgets.QAbstractSpinBox)
    p=widget; depth=0
    while p is not None and depth<20:
        try:
            if isinstance(p,editable): return True
            if isinstance(p,QtWidgets.QComboBox) and p.isEditable(): return True
            cls=str(p.metaObject().className()).lower() if hasattr(p,"metaObject") else ""
            if any(x in cls for x in ("lineedit","textedit","spinbox")): return True
            if "combobox" in cls and hasattr(p,"isEditable") and p.isEditable(): return True
            p=p.parentWidget(); depth+=1
        except Exception: break
    return False


class ShortcutPalette(QtWidgets.QFrame):
    def __init__(self,parent=None):
        super().__init__(parent,QtCore.Qt.Popup|QtCore.Qt.FramelessWindowHint)
        self.setObjectName("SolidFlowShortcutPalette"); self.setAttribute(QtCore.Qt.WA_DeleteOnClose,False)
        self.setStyleSheet("QFrame#SolidFlowShortcutPalette{border:1px solid palette(mid);border-radius:8px;background:palette(window);} QLabel#SolidFlowTitle{font-weight:700;padding:4px 5px;font-size:13px;} QLabel#SolidFlowSection{font-weight:600;padding:4px 3px 1px 3px;} QToolButton{min-width:120px;min-height:56px;padding:5px 8px;border-radius:6px;font-size:13px;text-align:left;} QToolButton:hover{background:palette(highlight);color:palette(highlighted-text);} QToolButton[solidflowSuggested='true']{font-weight:700;}")
        self.outer=QtWidgets.QVBoxLayout(self); self.outer.setContentsMargins(8,8,8,8); self.outer.setSpacing(4)
        self.title=QtWidgets.QLabel(); self.title.setObjectName("SolidFlowTitle"); self.outer.addWidget(self.title)
        self.host=QtWidgets.QWidget(); self.content=QtWidgets.QVBoxLayout(self.host); self.content.setContentsMargins(0,0,0,0); self.outer.addWidget(self.host)
    def _clear(self):
        while self.content.count():
            it=self.content.takeAt(0); w=it.widget(); w and w.deleteLater()
    def _section(self,title,specs):
        available=[s for s in specs if not s.command or _command_object(s.command) is not None]
        if not available: return
        lab=QtWidgets.QLabel(title); lab.setObjectName("SolidFlowSection"); self.content.addWidget(lab)
        w=QtWidgets.QWidget(); grid=QtWidgets.QGridLayout(w); grid.setContentsMargins(0,0,0,0); grid.setSpacing(4); cols=min(4,max(1,len(available)))
        for i,s in enumerate(available):
            b=QtWidgets.QToolButton(); b.setText(s.label); b.setToolButtonStyle(QtCore.Qt.ToolButtonTextBesideIcon); b.setIconSize(QtCore.QSize(28,28)); b.setProperty("solidflowSuggested",bool(s.emphasis)); b.setToolTip(s.tooltip)
            act=_command_action(s.command or s.icon_command)
            if act:
                try: b.setIcon(act.icon())
                except Exception: pass
            b.clicked.connect(lambda _c=False,x=s:self._trigger(x)); grid.addWidget(b,i//cols,i%cols)
        self.content.addWidget(w)
    def _trigger(self,s): self.hide(); QtCore.QTimer.singleShot(0,lambda:_run_spec(s))
    def rebuild(self):
        self._clear(); ctx=current_context(); self.title.setText("SolidFlow • "+ctx); a,b,c,d=_groups_for_context(ctx); self._section(a,b); self._section(c,d); self.adjustSize()
    def show_near_cursor(self):
        self.rebuild(); pos=QtGui.QCursor.pos(); self.adjustSize(); screen=QtWidgets.QApplication.screenAt(pos) or QtWidgets.QApplication.primaryScreen(); x,y=pos.x()+32,pos.y()+26
        if screen:
            g=screen.availableGeometry(); x=max(g.left()+8,min(x,g.right()-self.width()-8)); y=max(g.top()+8,min(y,g.bottom()-self.height()-8))
        self.move(x,y); self.show(); self.raise_(); self.activateWindow()


class ContextMiniToolbar(QtWidgets.QFrame):
    def __init__(self,parent=None):
        super().__init__(parent,QtCore.Qt.Tool|QtCore.Qt.FramelessWindowHint); self.setAttribute(QtCore.Qt.WA_ShowWithoutActivating,True); self.lay=QtWidgets.QHBoxLayout(self); self.lay.setContentsMargins(4,4,4,4)
    def show_for_selection(self):
        self.hide()
        if not auto_mini_toolbar_enabled() or _is_sketch_edit_mode(): return
        while self.lay.count():
            w=self.lay.takeAt(0).widget(); w and w.deleteLater()
        kind=_selection_kind(); specs=[]
        if kind=="Face": specs=[ActionSpec("Sketch",callback=create_sketch_on_face),ActionSpec("Fillet",callback=_fillet_best)]
        elif kind=="Edge": specs=[ActionSpec("Fillet",callback=_fillet_best),ActionSpec("Chamfer","PartDesign_Chamfer")]
        elif kind in ("Sketch","SketchEdges"): specs=[ActionSpec("Pad",callback=launch_pad),ActionSpec("Pocket",callback=launch_pocket),ActionSpec("Rivolvi",callback=_launch_rev_best)]
        elif kind=="Feature": specs=[ActionSpec("Modifica",callback=launch_edit_selected_feature),ActionSpec("Fillet",callback=_fillet_best)]
        if not specs: return
        for s in specs:
            b=QtWidgets.QToolButton(); b.setText(s.label); b.clicked.connect(lambda _c=False,x=s:_run_spec(x)); self.lay.addWidget(b)
        self.adjustSize(); p=QtGui.QCursor.pos()+QtCore.QPoint(18,20); self.move(p); self.show(); self.raise_(); QtCore.QTimer.singleShot(3500,self.hide)


class _SelectionObserver:
    def __init__(self,c): self.c=c
    def addSelection(self,*a): self.c.selection_changed()
    def removeSelection(self,*a): self.c.selection_changed()
    def clearSelection(self,*a): self.c.selection_changed()
    def setSelection(self,*a): self.c.selection_changed()


class SolidFlowController(QtCore.QObject):
    def __init__(self,mw):
        super().__init__(mw); self.main_window=mw; self.palette=ShortcutPalette(mw); self.mini=ContextMiniToolbar(mw); self.hint=self.mini
        self.viewbar=DisplayStyleBar(mw); self.enable_action=None; self.snap_action=None; self.viewbar_action=None; self.mini_action=None; self.references_action=None
        self.vtimer=QtCore.QTimer(self); self.vtimer.setInterval(450); self.vtimer.timeout.connect(self.viewbar.sync_position)
        self.stimer=QtCore.QTimer(self); self.stimer.setSingleShot(True); self.stimer.timeout.connect(self.mini.show_for_selection)
        self.observer=_SelectionObserver(self)
    def install(self):
        app=QtWidgets.QApplication.instance(); app and app.installEventFilter(self)
        self._install_menu(); self.vtimer.start(); Gui.Selection.addObserver(self.observer)
        if not _prefs().GetBool("Beta9ViewbarMigration",False): set_display_bar_enabled(True); _prefs().SetBool("Beta9ViewbarMigration",True)
        if smart_snap_enabled():
            try: apply_smart_snap_preferences()
            except Exception: pass
        QtCore.QTimer.singleShot(350,self.viewbar.sync_position)
    def _install_menu(self):
        global _menu
        bar=self.main_window.menuBar(); existing=None
        for a in bar.actions():
            if a.text().replace("&","")=="SolidFlow": existing=a.menu(); break
        _menu=existing or bar.addMenu("SolidFlow"); _menu.clear()
        a=_menu.addAction("Mostra palette"); a.setShortcut(QtGui.QKeySequence("Ctrl+Space")); a.triggered.connect(show_palette)
        _menu.addAction("Import Assistant",show_import_assistant); _menu.addAction("Impostazioni Smart Sketch…",show_smart_sketch_settings); _menu.addSeparator()
        self.enable_action=_menu.addAction("Usa tasto S"); self.enable_action.setCheckable(True); self.enable_action.triggered.connect(set_shortcut_enabled)
        self.snap_action=_menu.addAction("Smart Snap"); self.snap_action.setCheckable(True); self.snap_action.triggered.connect(set_smart_snap_enabled)
        self.mini_action=_menu.addAction("Mini-toolbar contestuale"); self.mini_action.setCheckable(True); self.mini_action.triggered.connect(set_auto_mini_toolbar_enabled)
        self.references_action=_menu.addAction("Auto-riferimenti faccia"); self.references_action.setCheckable(True); self.references_action.triggered.connect(set_auto_face_references_enabled)
        self.viewbar_action=_menu.addAction("Barra vista sotto cubo"); self.viewbar_action.setCheckable(True); self.viewbar_action.triggered.connect(self._toggle_viewbar)
        _menu.addSeparator(); _menu.addAction("Diagnostica SolidFlow…",show_diagnostics); self.sync_menu_state()
    def _toggle_viewbar(self,v): set_display_bar_enabled(v); self.viewbar.set_enabled(v); self.sync_menu_state()
    def sync_menu_state(self):
        for a,v in ((self.enable_action,shortcut_enabled()),(self.snap_action,smart_snap_enabled()),(self.mini_action,auto_mini_toolbar_enabled()),(self.references_action,auto_face_references_enabled()),(self.viewbar_action,display_bar_enabled())):
            if a: old=a.blockSignals(True); a.setChecked(bool(v)); a.blockSignals(old)
    def selection_changed(self): self.stimer.start(150)
    def eventFilter(self,watched,event):
        if event.type()!=QtCore.QEvent.KeyPress: return False
        try:
            if event.isAutoRepeat(): return False
        except Exception: pass
        if event.key()==QtCore.Qt.Key_Escape and self.palette.isVisible(): self.palette.hide(); return True
        if event.key()!=QtCore.Qt.Key_S or event.modifiers()!=QtCore.Qt.NoModifier or not shortcut_enabled(): return False
        app=QtWidgets.QApplication.instance()
        if not app: return False
        if _is_text_entry_widget(watched) or _is_text_entry_widget(app.focusWidget()): return False
        modal=app.activeModalWidget(); popup=app.activePopupWidget()
        if modal is not None and modal is not self.palette: return False
        if popup is not None and popup is not self.palette: return False
        self.mini.hide(); self.palette.hide() if self.palette.isVisible() else self.palette.show_near_cursor(); return True


def show_palette():
    if _controller: _controller.palette.hide() if _controller.palette.isVisible() else _controller.palette.show_near_cursor()

def show_diagnostics():
    status=getattr(App,"__solidflow_status__",{}) or {}; lines=["Core UI: "+VERSION,"FreeCAD: "+".".join(str(v) for v in App.Version()[:3]),"Context: "+current_context(),"Selection: "+_selection_kind(),"Tasto S: "+str(shortcut_enabled()),"Barra vista: "+str(display_bar_enabled())]
    for k in sorted(status): lines.append("%s: %s"%(k,status[k]))
    text="\n".join(lines); App.Console.PrintMessage("[SolidFlow diagnostics]\n"+text+"\n"); box=QtWidgets.QMessageBox(_controller.main_window if _controller else Gui.getMainWindow()); box.setWindowTitle("SolidFlow Diagnostics"); box.setText("Stato moduli SolidFlow"); box.setDetailedText(text); box.exec_()


def install():
    global _controller
    if _controller is not None: return _controller
    mw=Gui.getMainWindow()
    if mw is None: return None
    _controller=SolidFlowController(mw); _controller.install(); App.Console.PrintMessage("SolidFlow UX %s loaded. Press S.\n"%VERSION); return _controller
