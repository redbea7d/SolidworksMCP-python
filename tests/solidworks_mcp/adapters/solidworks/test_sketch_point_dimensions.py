"""Tests for point-to-point, centre-to-centre and construction sketch helpers."""

from types import SimpleNamespace

import pytest

from solidworks_mcp.adapters.solidworks import sketch as sk


class _Point:
    def __init__(self, x, y):
        self.X, self.Y, self.Z = x, y, 0.0
        self.selected = False


class _Circle:
    def __init__(self, x, y):
        self.centre = _Point(x, y)

    def GetCenterPoint2(self):
        return self.centre


class _Model:
    def __init__(self):
        self.selection = []
        self.calls = []
        self.SelectionManager = SimpleNamespace(
            GetSelectedObjectCount2=lambda mark: len(self.selection)
        )
        self.Extension = SimpleNamespace(SelectByID2=self._select_by_id)

    def _select_by_id(self, name, kind, *args):
        self.selection.append(name)
        return False  # the quirk: reports failure while selecting

    def ClearSelection2(self, _):
        self.selection.clear()

    def AddHorizontalDimension2(self, *xyz):
        self.calls.append(("horizontal", xyz))
        return "dim"

    def AddVerticalDimension2(self, *xyz):
        self.calls.append(("vertical", xyz))
        return "dim"

    def AddDimension2(self, *xyz):
        self.calls.append(("aligned", xyz))
        return "dim"


def _adapter(entities):
    model = _Model()
    values = []

    def select(target, append):
        if not append:
            model.selection.clear()
        model.selection.append(target)
        return False

    return SimpleNamespace(
        currentModel=model,
        _sketch_entities=entities,
        _sketch_entity_centers={},
        _attempt=lambda fn, default=None: _safe(fn, default),
        _get_attr_or_call=lambda obj, name: getattr(obj, name)(),
        _select_sketch_entity=select,
        _set_display_dimension_value=lambda d, v: values.append(v),
        _register_sketch_entity=lambda prefix, obj: f"{prefix}_9",
        constants={"swSmartDimensionDirectionUp": 0},
        values=values,
    )


def _safe(fn, default):
    try:
        return fn()
    except Exception:
        return default


@pytest.mark.parametrize(
    ("e1", "e2", "kind", "expected"),
    [
        ("Circle_1", "Circle_2", "linear", True),
        ("Line_1", "Circle_2", "linear", False),
        ("Line_1.start", "Circle_2", "linear", True),
        ("origin", "Circle_1", "linear", True),
        ("Line_1", None, "horizontal", True),
        ("Circle_1", None, "diameter", False),
    ],
)
def test_is_point_dimension(e1, e2, kind, expected):
    assert sk._is_point_dimension(None, e1, e2, kind) is expected


def test_horizontal_centre_to_centre_ignores_false_select_returns():
    adapter = _adapter({"Circle_1": _Circle(-0.0525, 0), "Circle_2": _Circle(0.0525, 0)})
    dim_id = sk._point_to_point_dimension(adapter, "Circle_1", "Circle_2", "horizontal", 105)
    assert dim_id == "Dimension_9"
    kind, xyz = adapter.currentModel.calls[0]
    assert kind == "horizontal"
    assert xyz[1] > 0  # text placed above the two centres
    assert adapter.values == [105]


def test_vertical_from_origin_selects_origin_point():
    adapter = _adapter({"Circle_1": _Circle(0, 0.0365)})
    sk._point_to_point_dimension(adapter, "origin", "Circle_1.center", "vertical", 36.5)
    assert adapter.currentModel.calls[0][0] == "vertical"
    assert adapter.currentModel.selection == []  # cleared after creation
    assert adapter.values == [36.5]


def test_unknown_point_name_is_a_clear_error():
    adapter = _adapter({"Circle_1": _Circle(0, 0)})
    with pytest.raises(Exception, match="Unknown point"):
        sk._point_to_point_dimension(adapter, "Circle_1.middle", "origin", "linear", 5)


def test_aligned_needs_a_second_point():
    adapter = _adapter({"Circle_1": _Circle(0, 0)})
    with pytest.raises(Exception, match="needs entity2"):
        sk._point_to_point_dimension(adapter, "Circle_1", None, "point_to_point", 5)


def test_set_construction_marks_each_rectangle_line():
    lines = [SimpleNamespace(ConstructionGeometry=False) for _ in range(4)]
    adapter = SimpleNamespace(
        currentSketchManager=object(),
        _sketch_entities={"Rectangle_1": lines},
        _attempt=lambda fn, default=None: _safe(fn, default),
        _handle_com_operation=lambda name, op: op(),
    )
    assert sk._set_sketch_construction_impl(adapter, "Rectangle_1", True) == "Rectangle_1"
    assert all(line.ConstructionGeometry for line in lines)
