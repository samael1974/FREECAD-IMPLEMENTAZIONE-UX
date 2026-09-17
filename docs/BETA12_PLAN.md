# SolidFlow UX 0.4.0-beta.12 — Stabilization / Sketch-on-face / External Geometry

## Goal
Beta12 is a stabilization and usability revision. Do not add unrelated large features before these workflows are reliable.

## User-reported issues to address

### 1. Sketch on inclined planar faces
- A sketch created on an inclined planar face can later be difficult for SolidFlow to recognise as the intended profile.
- A popup appears in the subsequent workflow and is not self-explanatory.
- Required behaviour: a mapped sketch must be recognised independently of face orientation and must stay associated with its support/body.
- Required diagnostics: show clearly which sketch/profile SolidFlow has detected, and never open an unexplained modal popup.

### 2. External geometry must be first-class for constraints
- When SolidFlow creates a sketch on a solid face, projected/reference geometry from the support must be usable directly for constraints in the active sketch.
- Internal sketch geometry + external edge should support context suggestions such as Coincident/Point-on-object, Parallel, Perpendicular, Tangent and distance where FreeCAD supports them.
- Internal circle + projected circular edge should suggest Concentric and relevant radius/diameter relationships where valid.
- Projected circular edges/holes should expose useful centres for snapping/constraint workflows.
- SolidFlow must never apply a constraint automatically; it only proposes 3–5 likely actions and the user confirms.

## Beta12 implementation priorities
1. Robust profile/sketch ownership detection for arbitrary planar mapped faces.
2. Clear profile context banner: sketch name, support face, body, mapped/unmapped state.
3. External-reference resolver shared by Smart Sketch and the S palette.
4. Constraint suggestion ranking that understands internal vs external geometry.
5. Better centre detection for projected circular edges/holes.
6. Avoid modal popup surprises; prefer side panel / compact contextual UI.
7. Regression tests for horizontal, vertical and inclined support faces.

## Focused test matrix

### A. Inclined face recognition
1. Create a wedge/prism with a planar inclined face.
2. Select inclined face -> SolidFlow -> Sketch on face.
3. Draw one closed circle and one closed rectangle.
4. Close Sketch.
5. Select Sketch in tree -> S.
6. Verify SolidFlow identifies the exact sketch and offers Profile/Pad/Pocket actions.
7. Reopen Sketch, close again, rotate model, repeat.

### B. External edge constraints
1. Sketch on planar face of a solid.
2. Verify support perimeter and circular-hole edges are projected/reference geometry.
3. Draw one line; select it + projected straight edge -> S.
4. Expect Parallel/Perpendicular/Coincident/Point-on-object suggestions as geometrically relevant.
5. Draw one circle; select it + projected circular edge -> S.
6. Expect Concentric and other valid circle-related suggestions.

### C. Hole-centre snap
1. Create a face with at least two cylindrical holes.
2. Sketch on that face.
3. Start Circle command and approach the projected hole centre.
4. Verify a clear centre snap/constraint cue is available and does not require manual construction geometry.

### D. Orientation regression
Repeat A/B/C on XY, XZ, YZ and at least one arbitrary planar inclined face.

## Information still needed from user
- Screenshot/text of the unexplained popup.
- Exact action that triggers it (press S, Extrude, select Sketch, close Sketch, etc.).
- Whether the inclined-face sketch was created through SolidFlow or native FreeCAD.
- Whether external references should be limited to the support face perimeter + holes, or also include nearby/non-coplanar geometry on demand.
