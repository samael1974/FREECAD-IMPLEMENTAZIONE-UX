"""Pure 2D sketch inference. Suggestions never modify the document."""
import math


def suggest(point, segments, tolerance, anchor=None):
    """Return one nearby endpoint, line extension, parallel or perpendicular hint.

    Segments contain (geometry index, start XY, end XY). Tolerance is in sketch
    units, calculated from screen pixels by the GUI. Degenerate edges are ignored.
    """
    candidates = []
    px, py = point
    for index, a, b in segments:
        dx, dy = b[0] - a[0], b[1] - a[1]
        length2 = dx * dx + dy * dy
        if length2 < 1e-16:
            continue
        for pos, endpoint in ((1, a), (2, b)):
            distance = math.hypot(px - endpoint[0], py - endpoint[1])
            if distance <= tolerance:
                candidates.append((0, distance, dict(kind='Coincident', reference=index,
                    position=pos, point=endpoint, guide=(endpoint, point))))
        t = ((px - a[0]) * dx + (py - a[1]) * dy) / length2
        projection = (a[0] + t * dx, a[1] + t * dy)
        distance = math.hypot(px - projection[0], py - projection[1])
        if (t < 0 or t > 1) and distance <= tolerance:
            candidates.append((1, distance, dict(kind='PointOnObject', reference=index,
                point=projection, guide=(a if t < 0 else b, projection))))
        if anchor is None:
            continue
        vx, vy = px - anchor[0], py - anchor[1]
        cursor_length = math.hypot(vx, vy)
        if cursor_length <= tolerance:
            continue
        for kind, ux, uy in (('Parallel', dx, dy), ('Perpendicular', -dy, dx)):
            factor = (vx * ux + vy * uy) / length2
            q = (anchor[0] + factor * ux, anchor[1] + factor * uy)
            distance = math.hypot(px - q[0], py - q[1])
            if distance <= tolerance and distance / cursor_length <= math.sin(math.radians(3)):
                candidates.append((2, distance, dict(kind=kind, reference=index, point=q,
                    guide=((anchor[0] - factor * ux * .25, anchor[1] - factor * uy * .25),
                           (anchor[0] + factor * ux * 1.25, anchor[1] + factor * uy * 1.25)))))
    return min(candidates, key=lambda c: (c[0], c[1]))[2] if candidates else None


def add_checked_constraint(sketch, constraint):
    """Reject only the proposed constraint if the native solver reports conflict."""
    index = sketch.addConstraint(constraint)
    try:
        if sketch.solve() == 0:
            return True
    except Exception:
        sketch.delConstraint(index)
        sketch.solve()
        raise
    sketch.delConstraint(index)
    if sketch.solve() != 0:
        raise RuntimeError('Il solver non torna valido dopo la rimozione del suggerimento')
    return False
