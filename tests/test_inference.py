import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'SolidFlowUX'))
from solidflow_inference import suggest, add_checked_constraint


class InferenceTests(unittest.TestCase):
    def test_oblique_extension(self):
        hint = suggest((20, 20.1), [(0, (0, 0), (10, 10))], .2)
        self.assertEqual(hint['kind'], 'PointOnObject')
        self.assertAlmostEqual(hint['point'][0], hint['point'][1])

    def test_extension_before_start(self):
        hint = suggest((-5, -.05), [(0, (0, 0), (10, 0))], .1)
        self.assertEqual(hint['guide'][0], (0, 0))
        self.assertEqual(hint['point'], (-5, 0))

    def test_no_extension_inside_segment(self):
        self.assertIsNone(suggest((5, .05), [(0, (0, 0), (10, 0))], .1))

    def test_parallel_and_perpendicular_oblique(self):
        segments = [(4, (0, 0), (10, 10))]
        for point, kind in [((20, 25.05), 'Parallel'), ((10, -4.95), 'Perpendicular')]:
            hint = suggest(point, segments, .2, (0, 5))
            self.assertEqual(hint['kind'], kind)
            self.assertEqual(hint['reference'], 4)

    def test_zoom_tolerance_and_angle_limit(self):
        segments = [(0, (0, 0), (10, 0))]
        self.assertIsNone(suggest((20, .3), segments, .2))
        self.assertIsNotNone(suggest((20, .3), segments, .4))
        self.assertIsNone(suggest((10, 8), segments, 2, (0, 5)))

    def test_endpoint_priority_and_degenerate_edge(self):
        hint = suggest((10.01, 10.01), [(0, (0, 0), (10, 10)), (1, (0, 0), (0, 0))], .1)
        self.assertEqual(hint['kind'], 'Coincident')
        self.assertEqual(hint['position'], 2)
        self.assertIsNone(suggest((0, 0), [(1, (0, 0), (0, 0))], 1))

    def test_far_cursor_and_no_geometry(self):
        self.assertIsNone(suggest((100, 40), [(0, (0, 0), (1, 1))], .1))
        self.assertIsNone(suggest((1, 1), [], 1))

    def test_solver_rejects_only_new_constraint(self):
        class Sketch:
            constraints = ['existing']
            def addConstraint(self, constraint):
                self.constraints.append(constraint)
                return len(self.constraints) - 1
            def delConstraint(self, index):
                self.constraints.pop(index)
            def solve(self):
                return -2 if len(self.constraints) > 1 else 0
        sketch = Sketch()
        self.assertFalse(add_checked_constraint(sketch, 'redundant'))
        self.assertEqual(sketch.constraints, ['existing'])

    def test_solver_accepts_constraint(self):
        class Sketch:
            def addConstraint(self, constraint): return 0
            def solve(self): return 0
            def delConstraint(self, index): raise AssertionError('must retain valid constraint')
        self.assertTrue(add_checked_constraint(Sketch(), 'parallel'))

if __name__ == '__main__':
    unittest.main()
