"""Tests for verified sketch selection (SelectByID2 returns False but selects)."""

from types import SimpleNamespace

from solidworks_mcp.adapters.solidworks.features import _select_sketch_verified


class _SelMgr:
    def __init__(self):
        self.count = 0
        self.EnableContourSelection = True

    def GetSelectedObjectCount2(self, mark):
        return self.count


def _model(select_by_id_selects: bool, feature_selects: bool):
    sel = _SelMgr()

    def select_by_id2(*args):
        if select_by_id_selects:
            sel.count = 1
        return False  # the quirk: always reports failure

    def feature_by_name(name):
        def select2(append, mark):
            if feature_selects:
                sel.count = 1
            return False
        return SimpleNamespace(Select2=select2)

    def clear(_):
        sel.count = 0

    return SimpleNamespace(
        SelectionManager=sel,
        ClearSelection2=clear,
        Extension=SimpleNamespace(SelectByID2=select_by_id2),
        FeatureByName=feature_by_name,
    )


def test_false_return_but_selected_is_success():
    m = _model(select_by_id_selects=True, feature_selects=False)
    assert _select_sketch_verified(SimpleNamespace(currentModel=m), "Sketch1") is None
    assert m.SelectionManager.EnableContourSelection is False


def test_falls_back_to_feature_select2():
    m = _model(select_by_id_selects=False, feature_selects=True)
    assert _select_sketch_verified(SimpleNamespace(currentModel=m), "Sketch1") is None


def test_reports_error_when_nothing_selected():
    m = _model(select_by_id_selects=False, feature_selects=False)
    err = _select_sketch_verified(SimpleNamespace(currentModel=m), "Sketch1")
    assert err and "Sketch1" in err
