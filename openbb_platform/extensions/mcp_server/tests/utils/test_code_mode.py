"""Tests for OpenBB code mode utilities."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pytest
from fastmcp.server.transforms.search import serialize_tools_for_output_markdown
from openbb_mcp_server.utils.code_mode import (
    OpenBBBM25SearchTransform,
    render_categories_as_markdown,
    serialize_openbb_tools_for_output_markdown,
    summarize_categories,
)


@dataclass
class FakeTool:
    """Minimal tool object for search and serialization tests."""

    name: str
    description: str
    parameters: dict[str, Any]
    output_schema: dict[str, Any] | None
    tags: set[str]


@pytest.mark.asyncio
async def test_bm25_search_transform_category_filter() -> None:
    """Test category filtering with explicit categories kwarg."""
    tools = [
        FakeTool(
            name="equity_price_historical",
            description="Get historical price data.",
            parameters={"type": "object", "properties": {"symbol": {"type": "string"}}},
            output_schema={
                "type": "object",
                "properties": {"results": {"type": "array"}},
            },
            tags={"equity", "price"},
        ),
        FakeTool(
            name="econometrics_panel_first_difference",
            description="First-difference estimate for panel data.",
            parameters={
                "type": "object",
                "properties": {"y_column": {"type": "string"}},
            },
            output_schema={
                "type": "object",
                "properties": {"results": {"type": "object"}},
            },
            tags={"econometrics"},
        ),
    ]

    transform = OpenBBBM25SearchTransform(max_results=5)
    results = await transform.search_tools(tools, "", categories={"econometrics"})

    assert len(results) == 1
    assert results[0].name == "econometrics_panel_first_difference"


@pytest.mark.asyncio
async def test_bm25_search_transform_category_filter_from_name_only() -> None:
    """Category filter works even when tool.tags is empty (inferred from tool name)."""
    tools = [
        FakeTool(
            name="equity_price_historical",
            description="Get historical price data.",
            parameters={"type": "object", "properties": {"symbol": {"type": "string"}}},
            output_schema={
                "type": "object",
                "properties": {"results": {"type": "array"}},
            },
            tags=set(),  # no tags — category must come from name
        ),
        FakeTool(
            name="economy_indicators",
            description="Get economic indicators.",
            parameters={
                "type": "object",
                "properties": {"country": {"type": "string"}},
            },
            output_schema={
                "type": "object",
                "properties": {"results": {"type": "array"}},
            },
            tags=set(),
        ),
    ]

    transform = OpenBBBM25SearchTransform(max_results=5)
    results = await transform.search_tools(tools, "", categories={"equity"})

    assert len(results) == 1
    assert results[0].name == "equity_price_historical"


@pytest.mark.asyncio
async def test_bm25_search_transform_tag_filter() -> None:
    """Test tag filtering with explicit tags kwarg."""
    tools = [
        FakeTool(
            name="equity_price_historical",
            description="Get historical price data.",
            parameters={"type": "object", "properties": {"symbol": {"type": "string"}}},
            output_schema={
                "type": "object",
                "properties": {"results": {"type": "array"}},
            },
            tags={"equity", "price"},
        ),
        FakeTool(
            name="equity_fundamental_metrics",
            description="Get fundamental metrics.",
            parameters={"type": "object", "properties": {"symbol": {"type": "string"}}},
            output_schema={
                "type": "object",
                "properties": {"results": {"type": "array"}},
            },
            tags={"equity", "fundamental"},
        ),
    ]

    transform = OpenBBBM25SearchTransform(max_results=5)
    results = await transform.search_tools(tools, "metrics", tags={"fundamental"})

    assert len(results) == 1
    assert results[0].name == "equity_fundamental_metrics"


@pytest.mark.asyncio
async def test_bm25_search_transform_subcategory_filter_from_name_only() -> None:
    """Subcategory filter works even when tool.tags is empty (from tool name)."""
    tools = [
        FakeTool(
            name="equity_price_historical",
            description="Get historical price data.",
            parameters={"type": "object", "properties": {"symbol": {"type": "string"}}},
            output_schema={
                "type": "object",
                "properties": {"results": {"type": "array"}},
            },
            tags=set(),  # no tags - subcategory must come from name
        ),
        FakeTool(
            name="equity_fundamental_metrics",
            description="Get fundamental metrics.",
            parameters={"type": "object", "properties": {"symbol": {"type": "string"}}},
            output_schema={
                "type": "object",
                "properties": {"results": {"type": "array"}},
            },
            tags=set(),
        ),
    ]

    transform = OpenBBBM25SearchTransform(max_results=5)
    results = await transform.search_tools(
        tools,
        "",
        categories={"equity"},
        tags={"price"},
    )

    assert len(results) == 1
    assert results[0].name == "equity_price_historical"


@pytest.mark.asyncio
async def test_bm25_search_transform_provider_filter() -> None:
    """Provider filters match provider tags from tool.tags."""
    tools = [
        FakeTool(
            name="equity_price_historical",
            description="Get historical price data from Intrinio.",
            parameters={"type": "object", "properties": {"symbol": {"type": "string"}}},
            output_schema={
                "type": "object",
                "properties": {"results": {"type": "array"}},
            },
            tags={"equity", "price", "intrinio"},
        ),
        FakeTool(
            name="equity_price_quote",
            description="Get quotes from FMP.",
            parameters={"type": "object", "properties": {"symbol": {"type": "string"}}},
            output_schema={
                "type": "object",
                "properties": {"results": {"type": "array"}},
            },
            tags={"equity", "price", "fmp"},
        ),
    ]

    transform = OpenBBBM25SearchTransform(max_results=5)
    results = await transform.search_tools(tools, "", tags={"intrinio"})

    assert len(results) == 1
    assert results[0].name == "equity_price_historical"


@pytest.mark.asyncio
async def test_bm25_search_transform_requested_max_results_is_capped() -> None:
    """Test requested max_results is capped by configured transform limit."""
    tools = [
        FakeTool(
            name=f"equity_price_tool_{i}",
            description="Price tool.",
            parameters={"type": "object", "properties": {"symbol": {"type": "string"}}},
            output_schema={"type": "object"},
            tags={"equity", "price"},
        )
        for i in range(10)
    ]

    transform = OpenBBBM25SearchTransform(max_results=3)
    results = await transform.search_tools(
        tools,
        "",
        categories={"equity"},
        requested_max_results=8,
    )

    assert len(results) == 3


@pytest.mark.asyncio
async def test_bm25_search_transform_requested_max_results_lower_than_cap() -> None:
    """Test requested max_results can be lower than configured cap."""
    tools = [
        FakeTool(
            name=f"equity_price_tool_{i}",
            description="Price tool.",
            parameters={"type": "object", "properties": {"symbol": {"type": "string"}}},
            output_schema={"type": "object"},
            tags={"equity", "price"},
        )
        for i in range(10)
    ]

    transform = OpenBBBM25SearchTransform(max_results=30)
    results = await transform.search_tools(
        tools,
        "",
        categories={"equity"},
        requested_max_results=5,
    )

    assert len(results) == 5


def test_summarize_categories() -> None:
    """Test category summary output with counts."""
    tools = [
        FakeTool(
            name="equity_price_historical",
            description="Get historical price data.",
            parameters={"type": "object"},
            output_schema={"type": "object"},
            tags={"equity", "price"},
        ),
        FakeTool(
            name="equity_fundamental_metrics",
            description="Get fundamental metrics.",
            parameters={"type": "object"},
            output_schema={"type": "object"},
            tags={"equity", "fundamental"},
        ),
        FakeTool(
            name="crypto_price_historical",
            description="Get crypto historical price data.",
            parameters={"type": "object"},
            output_schema={"type": "object"},
            tags={"crypto", "price"},
        ),
    ]

    categories = summarize_categories(tools, categories=set(), tags=set())

    assert categories == [
        {"category": "equity", "tool_count": 2},
        {"category": "crypto", "tool_count": 1},
    ]


def test_summarize_subcategories() -> None:
    """Test subcategory summary output with counts from tool names."""
    tools = [
        FakeTool(
            name="equity_price_historical",
            description="Get historical price data.",
            parameters={"type": "object"},
            output_schema={"type": "object"},
            tags=set(),
        ),
        FakeTool(
            name="equity_price_quote",
            description="Get latest quote.",
            parameters={"type": "object"},
            output_schema={"type": "object"},
            tags=set(),
        ),
        FakeTool(
            name="equity_fundamental_metrics",
            description="Get fundamental metrics.",
            parameters={"type": "object"},
            output_schema={"type": "object"},
            tags=set(),
        ),
        FakeTool(
            name="crypto_price_historical",
            description="Get crypto historical price data.",
            parameters={"type": "object"},
            output_schema={"type": "object"},
            tags=set(),
        ),
    ]

    categories = summarize_categories(
        tools,
        categories={"equity"},
        tags=set(),
        subcategory_mode=True,
    )

    assert categories == [
        {"category": "price", "tool_count": 2},
        {"category": "fundamental", "tool_count": 1},
    ]


def test_render_categories_as_markdown() -> None:
    """Test markdown rendering for category listing mode."""
    rendered = render_categories_as_markdown(
        [
            {"category": "equity", "tool_count": 12},
            {"category": "crypto", "tool_count": 8},
        ]
    )

    assert "### Available Categories" in rendered
    assert "`equity` (12 tools)" in rendered
    assert "`crypto` (8 tools)" in rendered


def test_fastmcp_render_tools_as_markdown() -> None:
    """Test FastMCP markdown rendering for search results."""
    tool = FakeTool(
        name="econometrics_panel_first_difference",
        description=(
            "Perform a first-difference estimate for panel data. "
            "Removes time-invariant entity effects by differencing."
        ),
        parameters={
            "type": "object",
            "properties": {
                "y_column": {
                    "type": "string",
                    "description": "Dependent variable column.",
                },
                "x_columns": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Regressor columns.",
                },
                "data": {
                    "type": "array",
                    "items": {"type": "object"},
                    "description": "Input rows.",
                },
            },
            "required": ["y_column", "x_columns", "data"],
        },
        output_schema={
            "type": "object",
            "properties": {
                "id": {"type": "string"},
                "results": {"type": "object"},
                "warnings": {"type": "array", "items": {"type": "object"}},
            },
        },
        tags={"econometrics"},
    )

    rendered = serialize_tools_for_output_markdown([tool])

    assert "### econometrics_panel_first_difference" in rendered
    assert "**Parameters**" in rendered
    assert "**Returns**" in rendered
    assert "`y_column` (string, required)" in rendered
    assert "`results` (object)" in rendered


def test_openbb_markdown_serializer_adds_dynamic_results_hint() -> None:
    """Test OpenBB markdown serializer adds dynamic Data-row hint."""
    tool = FakeTool(
        name="technical_fisher",
        description="Perform the Fisher Transform.",
        parameters={"type": "object", "properties": {"data": {"type": "array"}}},
        output_schema={
            "type": "object",
            "properties": {
                "results": {
                    "anyOf": [
                        {"type": "array", "items": {"$ref": "#/$defs/Data"}},
                        {"type": "null"},
                    ]
                }
            },
            "$defs": {
                "Data": {
                    "type": "object",
                    "properties": {},
                    "additionalProperties": True,
                }
            },
        },
        tags={"technical"},
    )

    rendered = serialize_openbb_tools_for_output_markdown([tool])

    assert "**OpenBB Result Hints**" in rendered
    assert "dynamic objects" in rendered


def test_openbb_markdown_serializer_adds_model_and_common_fields_hints() -> None:
    """Test OpenBB markdown serializer summarizes provider unions."""
    tool = FakeTool(
        name="equity_price_historical",
        description="Get historical price data.",
        parameters={"type": "object", "properties": {"symbol": {"type": "string"}}},
        output_schema={
            "type": "object",
            "properties": {
                "results": {
                    "anyOf": [
                        {
                            "type": "array",
                            "items": {
                                "anyOf": [
                                    {"$ref": "#/$defs/ProviderA"},
                                    {"$ref": "#/$defs/ProviderB"},
                                ]
                            },
                        },
                        {"type": "null"},
                    ]
                }
            },
            "$defs": {
                "ProviderA": {
                    "type": "object",
                    "properties": {
                        "date": {"type": "string"},
                        "open": {"type": "number"},
                    },
                },
                "ProviderB": {
                    "type": "object",
                    "properties": {
                        "date": {"type": "string"},
                        "open": {"type": "number"},
                        "close": {"type": "number"},
                    },
                },
            },
        },
        tags={"equity"},
    )

    rendered = serialize_openbb_tools_for_output_markdown([tool])

    assert "**OpenBB Result Hints**" in rendered
    assert "`ProviderA`" in rendered
    assert "`ProviderB`" in rendered
    assert "common `results` fields" in rendered
    assert "`date`" in rendered
    assert "`open`" in rendered
