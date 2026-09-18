"""Shared native-feature compatibility and preview rollback state (no Qt)."""


def set_feature_sides(feature, symmetric=False, reversed=False):
    """Use FreeCAD's enumeration labels, not version-dependent numeric indices."""
    if "SideType" in feature.PropertiesList:
        feature.SideType = "Symmetric" if symmetric else "One side"
    elif "Midplane" in feature.PropertiesList:
        feature.Midplane = bool(symmetric)
    if "Reversed" in feature.PropertiesList:
        feature.Reversed = bool(reversed)


class PreviewTransaction:
    """Own one preview transaction and restore only its affected objects.

    Capture before creating objects: native PartDesign can hide the old tip as
    soon as a preview is created. Names survive abortTransaction invalidating
    Python wrappers. GUI visibility is explicitly restored after abort.
    """

    def __init__(self, doc, objects=(), body=None):
        self.doc = doc
        self.body_name = body.Name if body else None
        tip = getattr(body, "Tip", None)
        self.tip_name = tip.Name if tip else None
        self.visibility = {}
        affected = list(objects) + (list(body.Group) + [body] if body else [])
        for obj in affected:
            if obj is not None and getattr(obj, "ViewObject", None) is not None:
                self.visibility[obj.Name] = bool(obj.ViewObject.Visibility)
        self.active = False

    def begin(self, label):
        self.doc.openTransaction(label)
        self.active = True

    def commit(self):
        if self.active:
            self.doc.commitTransaction()
            self.active = False

    def rollback(self):
        if not self.active:
            return
        # Do not silently claim success if FreeCAD cannot abort the transaction.
        self.doc.abortTransaction()
        self.active = False
        body = self.doc.getObject(self.body_name) if self.body_name else None
        if body is not None:
            body.Tip = self.doc.getObject(self.tip_name) if self.tip_name else None
        self.doc.recompute()
        for name, visible in self.visibility.items():
            obj = self.doc.getObject(name)
            if obj is not None and getattr(obj, "ViewObject", None) is not None:
                obj.ViewObject.Visibility = visible
