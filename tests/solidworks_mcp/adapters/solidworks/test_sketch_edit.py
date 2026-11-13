"""edit_sketch opens an existing sketch and registers its segments."""

from types import SimpleNamespace

from solidworks_mcp.adapters.solidworks import sketch as sk


class _Pt:
    def __init__(self, x, y):
        self.X, self.Y, self.Z = x, y, 0.0


class _Line:
    ConstructionGeometry = False

    def __init__(self, a, b):
        self.a, self.b = a, b

    def GetType(self):
        return 0

    def GetStartPoint2(self):
        return _Pt(*self.a)

    def GetEndPoint2(self):
        return _Pt(*self.b)


class _Circle:
    ConstructionGeometry = False

    def __init__(self, c, r):
        self.c, self.r = c, r

    def GetType(self):
        return 1

    def IsCircle(self):
        return True

    def GetCenterPoint2(self):
        return _Pt(*self.c)

    def GetRadius(self):
        return self.r


def _safe(fn, default=None):
    try:
        return fn()
    except Exception:
        return default


def _adapter(sketch_names, segments, active=None):
    sketch = SimpleNamespace(GetSketchSegments=lambda: segments)
    calls = []
    model = SimpleNamespace(
        GetActiveSketch2=lambda: active,
        EditSketch=lambda: calls.append("edit"),
        SketchManager=SimpleNamespace(ActiveSketch=sketch, AddToDB=False),
        ClearSelection2=lambda _: None,
    )
    registry, centres = {}, {}

    def register(prefix, obj):
        entity_id = f"{prefix}_{len(registry) + 1}"
        registry[entity_id] = obj
        return entity_id

    adapter = SimpleNamespace(
        currentModel=model,
        currentSketchManager=None,
        currentSketch=None,
        _attempt=_safe,
        _get_attr_or_call=lambda o, n: getattr(o, n)(),
        _register_sketch_entity=register,
        _reset_sketch_entity_registry=lambda: (registry.clear(), centres.clear()),
        _sketch_entities=registry,
        _sketch_entity_centers=centres,
        _handle_com_operation=lambda name, op: op(),
        calls=calls,
    )
    return adapter


def test_edit_sketch_registers_lines_and_circles(monkeypatch):
    from solidworks_mcp.adapters.solidworks import features

    monkeypatch.setattr(features, "_profile_feature_names", lambda a: ["Bolt Holes"])
    monkeypatch.setattr(features, "_select_sketch_verified", lambda a, n: None)
    adapter = _adapter(
        ["Bolt Holes"],
        [_Circle((-0.0525, 0), 0.0065), _Circle((0.0525, 0), 0.0065), _Line((0, 0), (0.01, 0))],
    )
    data = sk._edit_sketch_impl(adapter, "bolt holes")
    assert data["sketch"] == "Bolt Holes"
    ids = [e["id"] for e in data["entities"]]
    assert ids == ["Circle_1", "Circle_2", "Line_3"]
    assert data["entities"][0]["diameter"] == 13.0
    assert data["entities"][0]["center"] == {"x": -52.5, "y": 0.0}
    assert data["entities"][2]["length"] == 10.0
    assert adapter._sketch_entity_centers["Circle_2"] == (52.5, 0.0)
    assert adapter.currentSketchManager is not None
    assert adapter.calls == ["edit"]


def test_edit_sketch_refuses_while_another_sketch_is_open(monkeypatch):
    adapter = _adapter([], [], active=object())
    try:
        sk._edit_sketch_impl(adapter, "Bolt Holes")
    except Exception as exc:
        assert "exit_sketch" in str(exc)
    else:
        raise AssertionError("expected an error")


def test_edit_sketch_unknown_name_lists_sketches(monkeypatch):
    from solidworks_mcp.adapters.solidworks import features

    monkeypatch.setattr(features, "_profile_feature_names", lambda a: ["Base Sketch"])
    adapter = _adapter([], [])
    try:
        sk._edit_sketch_impl(adapter, "Nope")
    except Exception as exc:
        assert "Base Sketch" in str(exc)
    else:
        raise AssertionError("expected an error")
