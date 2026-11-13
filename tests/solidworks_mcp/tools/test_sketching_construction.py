"""The construction flag on add_line/add_circle/add_rectangle reaches the adapter."""

from types import SimpleNamespace

import pytest

from solidworks_mcp.adapters.base import AdapterResult, AdapterResultStatus
from solidworks_mcp.tools.sketching import _apply_construction


@pytest.mark.asyncio
async def test_construction_true_calls_the_adapter():
    calls = []

    async def setter(entity_id, construction):
        calls.append((entity_id, construction))
        return AdapterResult(status=AdapterResultStatus.SUCCESS, data=entity_id)

    await _apply_construction(SimpleNamespace(set_sketch_construction=setter), "Line_5", True)
    assert calls == [("Line_5", True)]


@pytest.mark.asyncio
async def test_construction_false_does_nothing():
    await _apply_construction(SimpleNamespace(), "Line_5", False)


@pytest.mark.asyncio
async def test_adapter_without_support_is_an_error_not_a_real_line():
    with pytest.raises(RuntimeError, match="construction"):
        await _apply_construction(SimpleNamespace(), "Line_5", True)
