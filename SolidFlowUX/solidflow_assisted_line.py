"""Opt-in assisted polyline with transient Coin guides and native constraints."""
import math
import FreeCAD as App
import FreeCADGui as Gui
import Part
import Sketcher
from pivy import coin
from PySide import QtCore, QtWidgets
from solidflow_inference import suggest, add_checked_constraint

_tool = None
LABELS = {'Coincident': 'Coincidente', 'PointOnObject': 'Sul prolungamento',
          'Parallel': 'Parallela', 'Perpendicular': 'Perpendicolare'}


class AssistedLine:
    def __init__(self, sketch):
        self.sketch = sketch
        self.doc = sketch.Document
        self.view = Gui.activeDocument().activeView()
        self.placement = sketch.getGlobalPlacement()
        self.anchor = None
        self.start_hint = None
        self.previous = None
        self.count = sketch.GeometryCount
        self.callbacks = []
        self.root = None
        self.panel = None
        self.timer = None
        self.closed = False

    def start(self):
        if self.view.getCameraType() != 'Orthographic':
            raise RuntimeError('Seleziona la vista ortografica prima di usare Linea assistita')
        self.scene = self.view.getSceneGraph()
        self.root = coin.SoSeparator()
        pick = coin.SoPickStyle(); pick.style = coin.SoPickStyle.UNPICKABLE
        self.root.addChild(pick)
        color = coin.SoBaseColor(); color.rgb = (0.9, 0.55, 0.05)
        self.root.addChild(color)
        style = coin.SoDrawStyle(); style.linePattern = 0xF0F0; style.lineWidth = 2
        self.root.addChild(style)
        self.coords = coin.SoCoordinate3(); self.lines = coin.SoLineSet()
        self.root.addChild(self.coords); self.root.addChild(self.lines)
        self.scene.addChild(self.root)
        self.panel = QtWidgets.QDockWidget('SolidFlow — Linea assistita', Gui.getMainWindow())
        self.panel.setObjectName('SolidFlowAssistedLine')
        content = QtWidgets.QWidget(); layout = QtWidgets.QVBoxLayout(content)
        self.label = QtWidgets.QLabel('Clic: primo punto. Esc o clic destro: termina.'); self.label.setWordWrap(True)
        layout.addWidget(self.label)
        self.constraints = QtWidgets.QCheckBox('Conferma il vincolo suggerito al clic')
        self.constraints.setChecked(True); layout.addWidget(self.constraints)
        layout.addWidget(QtWidgets.QLabel('Shift: punto libero senza snap né vincolo.'))
        finish = QtWidgets.QPushButton('Termina linea assistita'); finish.clicked.connect(self.stop)
        layout.addWidget(finish); self.panel.setWidget(content)
        Gui.getMainWindow().addDockWidget(QtCore.Qt.RightDockWidgetArea, self.panel)
        # Closing the panel also releases the input callbacks.
        self.panel.visibilityChanged.connect(lambda visible: self.stop() if not visible else None)
        self.panel.show()
        for event_type in (coin.SoLocation2Event, coin.SoMouseButtonEvent, coin.SoKeyboardEvent):
            type_id = event_type.getClassTypeId()
            callback = self.view.addEventCallbackPivy(type_id, self.event)
            self.callbacks.append((type_id, callback))
        self.timer = QtCore.QTimer(self.panel); self.timer.setInterval(200)
        self.timer.timeout.connect(self.check_context); self.timer.start()

    def check_context(self):
        if self.closed:
            return
        try:
            edit = Gui.activeDocument().getInEdit() if Gui.activeDocument() else None
            if not edit or edit.Object.Name != self.sketch.Name or edit.Object.Document.Name != self.doc.Name:
                self.stop(); return
            if self.sketch.GeometryCount != self.count:
                # Undo or another editing command invalidates geometry indices.
                self.anchor = self.previous = self.start_hint = None
                self.count = self.sketch.GeometryCount
                self.lines.numVertices.setValues(0, 1, [0])
                self.label.setText('Sketch modificato: clic per un nuovo primo punto.')
        except Exception:
            self.stop()

    def local_point(self, x, y):
        # getPoint returns a point on the camera focal plane. Intersect its ray
        # with the actual sketch plane (also valid for inclined/attached sketches).
        p = self.view.getPoint(x, y)
        direction = self.view.getViewDirection()
        normal = self.placement.Rotation.multVec(App.Vector(0, 0, 1))
        denom = normal.dot(direction)
        if abs(denom) < 1e-8:
            raise RuntimeError('Guarda lo Sketch frontalmente prima di disegnare')
        hit = p + direction * (normal.dot(self.placement.Base - p) / denom)
        q = self.placement.inverse().multVec(hit)
        return (q.x, q.y)

    def segments(self):
        return [(i, (g.StartPoint.x, g.StartPoint.y), (g.EndPoint.x, g.EndPoint.y))
                for i, g in enumerate(self.sketch.Geometry) if isinstance(g, Part.LineSegment)]

    def pointer(self, event):
        x, y = event.getPosition().getValue()
        point = self.local_point(x, y)
        adjacent = self.local_point(x + 8, y)
        tolerance = max(1e-8, math.dist(point, adjacent))
        hint = None if event.wasShiftDown() else suggest(point, self.segments(), tolerance, self.anchor)
        return hint['point'] if hint else point, hint

    def draw(self, point, hint):
        edges = []
        if hint:
            edges.append(hint['guide'])
        if self.anchor:
            edges.append((self.anchor, point))
        points = []
        for edge in edges:
            for x, y in edge:
                p = self.placement.multVec(App.Vector(x, y, 0))
                points.append((p.x, p.y, p.z))
        self.coords.point.setValues(0, len(points), points)
        self.lines.numVertices.setValues(0, len(edges) or 1, [2] * len(edges) if edges else [0])
        # Shrink the Coin array when switching from two guides to one.
        self.lines.numVertices.setNum(len(edges) or 1)
        text = LABELS[hint['kind']] + ' — linea %d' % (hint['reference'] + 1) if hint else 'Punto libero'
        self.label.setText(text + '\nClic per confermare; Shift per ignorare; Esc per terminare.')
        self.view.redraw()

    def event(self, callback):
        if self.closed:
            return
        event = callback.getEvent()
        try:
            if isinstance(event, coin.SoKeyboardEvent):
                if event.getKey() == coin.SoKeyboardEvent.ESCAPE:
                    callback.setHandled(); QtCore.QTimer.singleShot(0, self.stop)
                return
            if isinstance(event, coin.SoMouseButtonEvent):
                if event.getButton() == coin.SoMouseButtonEvent.BUTTON2:
                    callback.setHandled(); QtCore.QTimer.singleShot(0, self.stop); return
                if event.getButton() != coin.SoMouseButtonEvent.BUTTON1:
                    return  # Preserve wheel and native middle-button navigation.
                callback.setHandled()
                if event.getState() != coin.SoButtonEvent.DOWN:
                    return
                self.check_context()
                if self.closed:
                    return
                point, hint = self.pointer(event)
                self.confirm(point, hint, event.wasShiftDown())
            elif isinstance(event, coin.SoLocation2Event):
                self.check_context()
                if self.closed:
                    return
                point, hint = self.pointer(event)
                self.draw(point, hint)
                callback.setHandled()
        except Exception as exc:
            App.Console.PrintError('SolidFlow Linea assistita: %s\n' % exc)
            self.label.setText('Errore: %s. Esc per terminare.' % exc)
            QtCore.QTimer.singleShot(0, self.stop)

    def hint_constraint(self, index, position, hint):
        if hint['kind'] == 'Coincident':
            return Sketcher.Constraint('Coincident', index, position, hint['reference'], hint['position'])
        if hint['kind'] == 'PointOnObject':
            return Sketcher.Constraint('PointOnObject', index, position, hint['reference'])
        return Sketcher.Constraint(hint['kind'], index, hint['reference'])

    def confirm(self, point, hint, free=False):
        if self.anchor is None:
            self.anchor = point
            self.start_hint = hint if self.constraints.isChecked() and not free else None
            return
        if math.dist(self.anchor, point) < 1e-7:
            return
        if self.sketch.solve() != 0:
            self.label.setText('Risolvi prima i vincoli in conflitto nello Sketch.'); return
        self.doc.openTransaction('SolidFlow Linea assistita')
        try:
            index = self.sketch.addGeometry(Part.LineSegment(App.Vector(*self.anchor, 0), App.Vector(*point, 0)), False)
            proposed = []
            if self.constraints.isChecked() and not free:
                if self.previous is not None:
                    proposed.append(Sketcher.Constraint('Coincident', index, 1, self.previous, 2))
                elif self.start_hint:
                    proposed.append(self.hint_constraint(index, 1, self.start_hint))
                if hint:
                    proposed.append(self.hint_constraint(index, 2, hint))
            rejected = 0
            for constraint in proposed:
                if not add_checked_constraint(self.sketch, constraint):
                    rejected += 1
            self.doc.recompute()
            if self.sketch.solve() != 0:
                raise RuntimeError('Il solver segnala un conflitto; segmento annullato')
            end = self.sketch.Geometry[index].EndPoint
            self.doc.commitTransaction()
        except Exception:
            self.doc.abortTransaction()
            raise
        self.anchor = (end.x, end.y)
        self.previous = index
        self.start_hint = None
        self.count = self.sketch.GeometryCount
        if rejected:
            self.label.setText('Linea creata; suggerimento ridondante scartato dal solver.')

    def stop(self, *_):
        global _tool
        if self.closed:
            return
        self.closed = True
        if self.timer:
            self.timer.stop()
        for type_id, callback in self.callbacks:
            try: self.view.removeEventCallbackPivy(type_id, callback)
            except Exception: pass
        self.callbacks.clear()
        if self.root:
            try: self.scene.removeChild(self.root)
            except Exception: pass
        if self.panel:
            self.panel.hide(); self.panel.deleteLater()
        if _tool is self:
            _tool = None


def launch():
    global _tool
    import solidflow_smart
    sketch = solidflow_smart.active_sketch()
    if sketch is None or not sketch.isDerivedFrom('Sketcher::SketchObject'):
        QtWidgets.QMessageBox.information(Gui.getMainWindow(), 'Linea assistita', 'Apri prima uno Sketch in modifica.')
        return
    if _tool:
        _tool.stop()
    # Re-enter edit mode to finish any pending native drawing command before
    # installing our own input handler. Existing sketch geometry is preserved.
    Gui.activeDocument().resetEdit()
    Gui.activeDocument().setEdit(sketch.Name)
    _tool = AssistedLine(sketch)
    try:
        _tool.start()
    except Exception:
        _tool.stop()
        raise
