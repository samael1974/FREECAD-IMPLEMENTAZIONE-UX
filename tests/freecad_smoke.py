"""Run with FreeCADCmd tests/freecad_smoke.py (FreeCAD 1.1.x).

Uses only temporary documents. Raises on failure; prints PASS only at the end.
Also executable in FreeCAD's Python console with import runpy;
runpy.run_path(path). This is a kernel/transaction test, not GUI acceptance.
"""
import math
import sys
from pathlib import Path
import FreeCAD as App
import Part

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'SolidFlowUX'))
from solidflow_preview import PreviewTransaction, set_feature_sides


def check_shape(feature, volume):
    assert feature.isValid(), feature.Name
    assert not feature.Shape.isNull() and feature.Shape.isValid(), feature.Name
    assert abs(feature.Shape.Volume - volume) < 1e-5, (feature.Name, feature.Shape.Volume, volume)


def run():
    doc = App.newDocument('SolidFlowSmoke')
    doc.UndoMode = 1
    try:
        body = doc.addObject('PartDesign::Body', 'Body')
        sketch = body.newObject('Sketcher::SketchObject', 'Sketch')
        sketch.addGeometry(Part.Circle(App.Vector(), App.Vector(0, 0, 1), 10), False)
        for symmetric in (False, True):
            for reverse in (False, True):
                tx = PreviewTransaction(doc, [sketch], body)
                tx.begin('Pad smoke')
                pad = body.newObject('PartDesign::Pad', 'Pad')
                pad.Profile = sketch
                pad.Length = 20
                set_feature_sides(pad, symmetric, reverse)
                doc.recompute()
                check_shape(pad, math.pi * 100 * 20)
                bounds = pad.Shape.BoundBox
                low, high = (-10, 10) if symmetric else ((-20, 0) if reverse else (0, 20))
                assert abs(bounds.ZMin - low) < 1e-6 and abs(bounds.ZMax - high) < 1e-6
                tx.rollback()
        pad = body.newObject('PartDesign::Pad', 'BasePad')
        pad.Profile = sketch
        pad.Length = 20
        set_feature_sides(pad, True)
        doc.recompute()
        hole = body.newObject('Sketcher::SketchObject', 'HoleProfile')
        hole.addGeometry(Part.Circle(App.Vector(), App.Vector(0, 0, 1), 2), False)
        doc.recompute()
        # Real native Cancel and OK/Undo, alternating for 20 cycles.
        for cycle in range(20):
            before = {o.Name for o in doc.Objects}
            tip = body.Tip.Name
            tx = PreviewTransaction(doc, [hole], body)
            tx.begin('Pocket smoke')
            pocket = body.newObject('PartDesign::Pocket', 'Pocket')
            pocket.Profile = hole
            pocket.Length = 4
            set_feature_sides(pocket, bool(cycle % 2), bool((cycle // 2) % 2))
            doc.recompute()
            check_shape(pocket, math.pi * (2000 - 16))
            if cycle % 2:
                tx.commit()
                doc.undo()
                doc.recompute()
            else:
                tx.rollback()
            assert {o.Name for o in doc.Objects} == before
            assert body.Tip.Name == tip
        print('PASS: native Pad side modes and 20 Pocket Cancel/OK/Undo cycles')
    finally:
        App.closeDocument(doc.Name)


run()
