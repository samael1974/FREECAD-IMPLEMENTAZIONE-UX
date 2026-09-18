# SolidFlow UX — Beta 13 implementation brief for Astra Medium
Date: 2026-09-18
Target: FreeCAD 1.1.3, Windows x86-64, Python 3.11
Current release baseline: SolidFlow UX 0.4.0-beta.12

## Mission
SolidFlow UX is not a replacement CAD kernel. It is a UX/workflow layer over native FreeCAD objects and commands.
Primary goal: reduce clicks, ambiguity, modal interruptions, and learning friction while keeping the resulting model native/editable in FreeCAD.

Design rule:
> A feature enters SolidFlow only if it reduces clicks, reduces ambiguity, or makes FreeCAD easier to understand.

Do not rebuild existing robust FreeCAD geometry algorithms unless necessary. Prefer native Sketcher/PartDesign features and wrap them with clearer context, preview, selection and PropertyManager-style UI.

## New external user feedback
A FreeCAD/Fusion user reported:
- difficulty discovering the sketch grid;
- sketch dimension colors are too visually strong and not practical;
- FreeCAD mouse navigation cannot be made to feel like Fusion default.

Interpretation: the problem is partly discoverability, not missing functionality. FreeCAD already has Sketcher grid/snap and multiple navigation styles, but SolidFlow should expose the useful controls directly.

## New Federico test feedback
1. Sketch circular pattern must make quantity and angular extent obvious.
2. Rectangular X/Y patterns should make rows, columns and spacing obvious in both Sketch and 3D feature contexts.
3. Tree/model panel and Selection View should remain visible.
4. Fillets across edges meeting oblique faces need better corner handling / more homogeneous results.
5. Dimensions should use a much calmer visual language; driving dimensions should be near-black, not red/bright.
6. Patterning an existing 3D feature (Fillet, Boolean, Pocket, Pad, etc.) is not self-explanatory.
7. SolidFlow view controls under the navigation cube sometimes disappear.
8. 3D model visibility can disappear/reappear unpredictably during workflows.
9. Circles should expose four quadrant snap/inference points: top, bottom, left, right.
10. Current report output shows:
   - conflicting/redundant Sketch constraints;
   - deprecated PartDesign Midplane use. SolidFlow currently writes Midplane in FeaturePreviewDialog and must migrate to SideType where supported.

## Screenshots interpretation
The attached Fusion 360 screenshots show a strong interaction model worth borrowing:
- persistent workspace tabs (Solid, Surface, Mesh, Sheet Metal/Plastic, Utilities, Sketch);
- commands grouped by Create / Modify / Construct / Inspect / Insert;
- active Sketch keeps a compact Sketch Palette visible with Grid, Snap, Show Profile, Show Points, Show Dimensions, Show Constraints, Show Projected Geometry;
- the canvas remains the main interaction surface;
- pattern dialogs expose numeric parameters directly.

Do not copy Autodesk assets/icons. Copy interaction principles only.

## Research summary

### FreeCAD capabilities we should surface better
FreeCAD Sketcher already supports:
- per-sketch grid toggle, grid spacing and automatic grid spacing;
- snapping to grid, geometry, midpoints and angles;
- auto-constraints;
- external/projected geometry;
- independent Tree View and Selection View panels.

FreeCAD also supports multiple navigation styles, but there is no exact Fusion preset documented. Fusion default is:
- wheel = zoom;
- middle mouse drag = pan;
- Shift + middle mouse drag = orbit.

This should become a SolidFlow optional navigation preset, isolated and reversible.

### Fusion pattern UX
Fusion circular Sketch pattern exposes:
- Full / Angle / Symmetric distribution;
- total angle;
- quantity;
- direct canvas manipulators.

Fusion rectangular Sketch pattern exposes:
- Quantity per direction;
- Distance per direction;
- Extent or Spacing mode;
- One Direction / Symmetric.

Fusion 3D patterns can pattern faces, bodies, features, components or construction geometry.

### SolidWorks pattern UX
SolidWorks circular patterns expose:
- pattern axis;
- angle;
- number of instances;
- equal spacing over 360°;
- seed features/faces;
- skipped instances.

Linear Sketch Pattern exposes:
- X/Y spacing;
- number of instances;
- angle;
- entities to pattern;
- instances to skip.

### Fillet UX
Fusion provides:
- Tangent Chain toggle;
- G1 tangent / G2 curvature continuity;
- Rolling Ball / Setback corner type;
- variable/asymmetric radii;
- multiple selection sets.

SolidWorks Fillet/FilletXpert provides:
- edges/faces/features/loops selection;
- tangent propagation;
- full/partial preview;
- setback corners;
- continuously blended edges.

FreeCAD PartDesign Fillet is more limited. SolidFlow must therefore improve selection/diagnostics first, then offer fallback strategies only where native OCC/FreeCAD supports them.

## Beta 13 priorities

### P0 — correctness / stability

#### P0.1 Remove deprecated Midplane usage
Current target:
- `SolidFlowUX/solidflow_features.py`
- `FeaturePreviewDialog.update_preview()`

Problem:
- setting `Midplane=False` in current FreeCAD emits a deprecation warning;
- FeatureExtrude now uses `SideType`.

Required behavior:
- if `SideType` exists, use it instead of writing `Midplane`;
- one-side => SideType index/name corresponding to one side;
- symmetric => SideType corresponding to symmetric;
- preserve `Reversed`;
- only fall back to Midplane on versions that do not expose SideType.

Acceptance:
- Pad/Pocket preview and creation produce no Midplane deprecation warning on FreeCAD 1.1.3.
- Symmetric and reversed operations still create correct geometry.

#### P0.2 Viewbar persistence
Current target:
- `SolidFlowUX/solidflow_viewbar.py`

Problem:
- vertical bar under navigation cube disappears.

Likely cause:
- bar is reparented to the current MDI view host and only repositioned opportunistically.

Implement:
- robust event filter on MDI area / active 3D view for resize, show, activation and subwindow changes;
- periodic recovery timer only as a fallback, not primary mechanism;
- do not destroy/recreate the bar unnecessarily;
- bar must hide only when there is no active document or preference disables it.

Acceptance:
- switching documents, entering/exiting Sketch, resizing FreeCAD, changing workbench, maximizing/restoring subwindow: bar remains visible.
- no duplicate bars.

#### P0.3 3D visibility guard
Audit every SolidFlow workflow that touches `ViewObject.Visibility`.

Known risk:
- Fillet creation explicitly hides the base feature;
- profile previews create/remove temporary objects;
- workflow transitions can leave the wrong feature hidden.

Implement a transaction-safe visibility snapshot:
- before temporary preview: capture visibility of affected source objects;
- on Cancel/error: restore exactly;
- on successful PartDesign feature: allow native tip visibility behavior, but never hide unrelated objects;
- no temporary preview object may remain after cancel/undo.

Acceptance:
- 20 cycles of Pad/Pocket/Fillet/Profile Picker with Cancel/OK/Undo never cause model to disappear unexpectedly.

#### P0.4 Constraint conflict guard
Before invoking a constraint from SolidFlow Smart suggestions:
- inspect current selection and existing constraints when practical;
- do not automatically apply constraints;
- if native command reports redundancy/conflict, keep model unchanged and show concise SolidFlow guidance.

Do not try to replace the Sketcher solver.

### P1 — high-value UX

#### P1.1 SolidFlow Sketch Palette
Create a persistent lightweight side panel while a Sketch is in edit mode, inspired by Fusion but implemented with FreeCAD controls.

Minimum controls:
- Look normal to Sketch;
- Grid on/off;
- Snap on/off;
- Show profile shading;
- Show points;
- Show dimensions;
- Show constraints;
- Show projected/external geometry;
- Construction toggle;
- Auto-constraints on/off.

Goals:
- eliminate the “FreeCAD has no grid” discoverability problem;
- no nested menus for common Sketch state;
- panel remains small and does not replace the model tree.

Use native FreeCAD preferences/properties where available.

#### P1.2 Dimension visual preset
Current beta12 uses blue/grey constrained dimension colors.
User now wants SolidWorks-like visual quietness.

Implement a reversible SolidFlow preset:
- driving dimensions: near-black/dark graphite;
- reference/non-driving dimensions: muted blue-grey;
- fully constrained geometry: black/dark;
- under-defined geometry: blue;
- external geometry: purple remains useful;
- errors/conflicts: red only when there is an actual problem.

Do not globally recolor all UI text.

#### P1.3 Fusion-style mouse preset
Optional setting in SolidFlow Preferences:
`Navigazione mouse: FreeCAD | Fusion-like`

Fusion-like target:
- wheel = zoom;
- MMB drag = pan;
- Shift+MMB drag = orbit;
- orbit around cursor/selected pivot when possible.

Implementation notes:
- first verify whether a native FreeCAD navigation style can be configured to match exactly;
- if not, implement a narrowly-scoped event filter for the 3D view;
- must not interfere with Sketch geometry dragging, S shortcut, context menus or text inputs;
- setting must be reversible.

#### P1.4 Keep model tree + Selection View visible
FreeCAD already has Tree View and Selection View dock panels.

Implement command/preference:
`Layout SolidFlow`
- ensure Model/Tree panel visible on left;
- ensure Selection View visible below it or in a predictable dock;
- preserve user sizes where possible;
- do not permanently lock the user out of hiding them, but restore them at SolidFlow startup if the option is enabled.

Optional checkbox:
`Mantieni Albero + Selezione visibili`.

#### P1.5 Pattern UX simplification — one SolidFlow PatternManager
Do not replace native pattern geometry immediately.
Wrap native FreeCAD pattern capability with a consistent side PropertyManager.

Sketch circular:
- Entities selected
- Center
- Distribution: Full / Angle / Symmetric
- Total angle
- Copies/occurrences
- Equal constraints option
- live preview if practical

Sketch rectangular:
- Entities selected
- Direction X: quantity + spacing/extent
- Direction Y: quantity + spacing/extent
- one direction / symmetric where feasible
- clone/equal option in Advanced

Important FreeCAD limitation:
native Sketcher RectangularArray currently asks rows/columns first, then spacing is commonly edited via generated dimensional constraints. A custom SolidFlow wrapper may need to create/edit those constraints after the native array creation rather than rewriting the array engine.

3D linear/polar:
- object type should default to Feature when a PartDesign feature is selected;
- display the selected seed feature by readable label;
- Linear: direction, occurrences, length/spacing, optional second direction;
- Polar: axis, occurrences, overall angle/spacing;
- allow Pad, Pocket, Fillet, Chamfer, Hole and Boolean-like compatible PartDesign features where FreeCAD accepts them.

If a native PartDesign pattern cannot directly pattern another pattern, suggest MultiTransform instead of failing silently.

#### P1.6 Explain patternability in S palette
When a PartDesign feature is selected:
- show `Serie lineare 3D`
- show `Serie polare 3D`
- tooltip: “Ripeti questa lavorazione, non l’intero corpo”
- if unsupported selection: show reason, not a dead command.

### P1.7 Circle quadrant inference
Goal: top/bottom/left/right snap markers on circles and arcs while Sketching.

Do not add permanent construction points by default.

Implement transient inference markers:
- circle center C=(cx,cy), radius r;
- quadrant candidates:
  - right=(cx+r,cy)
  - left=(cx-r,cy)
  - top=(cx,cy+r)
  - bottom=(cx,cy-r)
- show marker only when cursor is within snap tolerance;
- include external/projected circular geometry.

On confirmation:
- prefer native constraints that preserve intent;
- a point/endpoint snapped to a quadrant can be represented with PointOnObject plus horizontal/vertical alignment relative to the circle center, when FreeCAD supports the selected loci;
- never create redundant constraints if auto-constraints already created the required relation.

Add icons/inference glyphs for:
- center;
- quadrant;
- tangent;
- midpoint;
- coincidence.

### P1.8 Fillet selection and corner quality
Current Fillet Doctor already supports direct edge picking and kernel testing.

Improve:
- default `Tangent chain` OFF;
- optional `Tangent chain` ON to add tangentially connected edges;
- group selected edges by shared vertices and face continuity;
- detect multi-edge corners (3+ selected edges meeting at one vertex);
- preview each corner and report which vertex/edge combination fails;
- try safe selection orders / subsets before declaring failure.

Do NOT claim G2/setback if native FreeCAD/OCC API does not support it through PartDesign::Fillet.

Possible fallback strategies for difficult oblique corners:
1. create the fillet in staged operations (one edge group, recompute, then next group);
2. test a smaller radius around the problematic vertex;
3. offer a “smooth corner strategy” experimental mode only if geometry validation passes;
4. for imported/simple solids, consider Part kernel operations outside PartDesign only as explicit advanced fallback.

Acceptance:
- user can select exactly the edges wanted;
- no automatic whole-chain expansion unless enabled;
- diagnostic names the failing edge/vertex group;
- no invalid feature is committed.

### P2 — after P0/P1 stabilizes

#### P2.1 PropertyManager migration
Replace modal Pad/Pocket/Revolution/Fillet/Sweep dialogs progressively with a docked SolidFlow PropertyManager:
- parameters left;
- model always orbitable/zoomable;
- live preview;
- OK / Cancel persistent;
- selection boxes can be filled by clicking canvas.

This is strategically more important than adding many new modeling commands.

#### P2.2 Workspace command grouping
Borrow the interaction concept from Fusion, not its artwork.

SolidFlow top-level functional groups:
- SOLIDO
- SUPERFICI
- MESH
- SCHIZZO
- STUDIO
- STAMPA 3D

Within active context use:
- CREA
- MODIFICA
- COSTRUZIONE
- VERIFICA
- INSERISCI

Keep S palette as the primary shortcut-driven interface. Ribbon-like groups are discoverability, not the main workflow.

#### P2.3 Appearance / D5 workflow
Do not build a fake photorealistic renderer.
SolidFlow Studio should:
- give better viewport material appearance;
- provide reusable material presets;
- support object and face assignment where feasible;
- prepare clean exports/material naming for D5 Render.

## Economicity / efficiency rules
1. Prefer native FreeCAD commands and object types.
2. One shared PropertyManager framework, not one unique UI architecture per feature.
3. One shared SelectionService for face/edge/feature/sketch classification.
4. One shared PreviewTransaction helper for visibility and Undo/Cancel.
5. Avoid monkey-patching new beta layers indefinitely; consolidate into stable modules.
6. Add FreeCADCmd runtime smoke tests before expanding aggressively.
7. Do not add a function because Fusion/SolidWorks has it; add it only when it improves the target beginner workflow.

## Recommended execution order for Astra Medium
1. Fix Midplane -> SideType.
2. Fix viewbar persistence.
3. Add visibility snapshot/restore helper and regression test.
4. Make dimensions near-black + reversible preset.
5. Ensure Tree/Selection panels persistent via SolidFlow layout option.
6. Add Sketch Palette with Grid/Snap/Profile/Dimensions/Constraints/Projected Geometry.
7. Implement Fusion-like mouse preset.
8. Implement quadrant inference markers.
9. Create shared PatternManager wrapper for Sketch circular/rectangular and 3D feature patterns.
10. Improve Fillet Doctor tangent-chain toggle and multi-edge corner diagnostics.
11. Begin docked PropertyManager framework.

## Minimum smoke test before publishing Beta 13
- Start FreeCAD 1.1.3 with no SolidFlow console errors.
- Create Body -> Sketch on planar and inclined face.
- Grid/Snap visible and toggleable from SolidFlow Sketch Palette.
- External geometry works and does not duplicate links.
- Circle quadrant markers appear and create a valid native constraint state.
- Smart dimension text is dark, readable and errors remain red.
- Pad one-side/symmetric/reversed: no Midplane deprecation warning.
- Rectangular Sketch pattern: rows/columns and spacing intent clear.
- Circular Sketch pattern: quantity and angular extent clear.
- Pattern a Pocket and a Fillet as 3D features.
- Fillet three meeting/oblique edges: diagnostic + valid result or clear reason.
- Switch workbenches/documents/Sketch edit: viewbar remains visible.
- Cancel/Undo repeated: no disappearing model and no orphan preview objects.
- Tree and Selection View remain available.
- Save, close, reopen FCStd and recompute without new SolidFlow warnings.

## Official references consulted
- FreeCAD Sketcher grid/snap/preferences:
  https://github.com/FreeCAD/FreeCAD-documentation/blob/main/wiki/Sketcher_Preferences.md
  https://github.com/FreeCAD/FreeCAD-documentation/blob/main/wiki/Sketcher_Grid.md
- FreeCAD mouse navigation:
  https://github.com/FreeCAD/FreeCAD-documentation/blob/main/wiki/Mouse_navigation.md
- FreeCAD Tree / Selection panels:
  https://github.com/FreeCAD/FreeCAD-documentation/blob/main/wiki/Tree_view.md
  https://github.com/FreeCAD/FreeCAD-documentation/blob/main/wiki/Selection_view.md
- FreeCAD Sketcher Rectangular Array:
  https://github.com/FreeCAD/FreeCAD-documentation/blob/main/wiki/Sketcher_RectangularArray.md
- FreeCAD Sketcher Rotate / polar transform:
  https://github.com/FreeCAD/FreeCAD-documentation/blob/main/wiki/Sketcher_Rotate.md
- FreeCAD PartDesign Polar Pattern:
  https://github.com/FreeCAD/FreeCAD-documentation/blob/main/wiki/PartDesign_PolarPattern.md
- Autodesk Fusion Sketch Palette:
  https://help.autodesk.com/view/fusion360/ENU/?contextId=SKT-3D-SKETCH
- Autodesk Fusion mouse preferences:
  https://help.autodesk.com/view/fusion360/ENU/?contextId=GS-SET-PREFERENCES
- Autodesk Fusion circular Sketch pattern:
  https://help.autodesk.com/cloudhelp/ENU/Fusion-Sketch/files/SKT-CREATE-CIRCULAR-PATTERN.htm
- Autodesk Fusion rectangular Sketch pattern:
  https://help.autodesk.com/cloudhelp/ENU/Fusion-Sketch/files/SKT-CREATE-RECTANGULAR-PATTERN.htm
- Autodesk Fusion 3D rectangular/circular patterns:
  https://help.autodesk.com/view/fusion360/ENU/?contextId=MODEL-RECTANGULAR-PATTERN-CMD
  https://help.autodesk.com/cloudhelp/ENU/Fusion-Model/files/GUID-195A1C75-1C94-47AE-A10F-DBCC17C2A212.htm
- Autodesk Fusion Fillet:
  https://help.autodesk.com/cloudhelp/ENU/Fusion-Model/files/SLD-REF-FILLET.htm
- SOLIDWORKS Sketch Snaps:
  https://help.solidworks.com/2025/english/SolidWorks/sldworks/c_sketch_snaps.htm
- SOLIDWORKS Circular Pattern:
  https://help.solidworks.com/2025/english/SolidWorks/sldworks/HIDD_CPATTERN.htm
- SOLIDWORKS Linear Sketch Pattern:
  https://help.solidworks.com/2025/English/SolidWorks/sldworks/HIDD_DVE_SKETCH_PATTERN_LINEAR.htm
- SOLIDWORKS Fillet / FilletXpert:
  https://help.solidworks.com/2026/English/SolidWorks/sldworks/HIDD_FILLET_MGR_ADD.htm

## Important restraint
Do not publish a new installer until the P0 fixes and smoke test pass. Keep planned vs implemented/tested clearly separated.
