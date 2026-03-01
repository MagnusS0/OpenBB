"""Code Mode helpers for OpenBB MCP."""

from __future__ import annotations

import inspect
from collections.abc import Sequence
from typing import Annotated, Any, Literal, cast

from fastmcp.experimental.transforms.code_mode import CodeMode
from fastmcp.server.context import Context
from fastmcp.server.transforms.search import (
    SearchResultSerializer,
    serialize_tools_for_output_json,
    serialize_tools_for_output_markdown,
)
from fastmcp.server.transforms.search.base import _extract_searchable_text
from fastmcp.server.transforms.search.bm25 import (
    BM25SearchTransform,
    _BM25Index,
    _catalog_hash,
)
from fastmcp.tools.tool import Tool
from fastmcp.utilities.logging import get_logger

logger = get_logger(__name__)
OPENBB_HINT_MAX_MODELS = 5
OPENBB_HINT_MAX_FIELDS = 8


def _tool_category_from_name(tool_name: str) -> str | None:
    """Infer top-level category from OpenBB tool name convention."""
    if "_" not in tool_name:
        return None
    return tool_name.split("_", maxsplit=1)[0].strip().lower() or None


def _tool_subcategory_from_name(tool_name: str) -> str | None:
    """Infer subcategory from OpenBB tool name convention (second segment)."""
    parts = tool_name.split("_", maxsplit=2)
    if len(parts) < 3:
        return None
    return parts[1].strip().lower() or None


def _tool_searchable_tags(tool: Tool) -> set[str]:
    """Collect normalized tags for filtering."""
    tags = {
        str(tag).strip().lower() for tag in (tool.tags or set()) if str(tag).strip()
    }
    if category := _tool_category_from_name(tool.name):
        tags.add(category)
    if subcategory := _tool_subcategory_from_name(tool.name):
        tags.add(subcategory)
    return tags


def _tool_matches_filters(
    tool: Tool,
    *,
    categories: set[str],
    tags: set[str],
) -> bool:
    """Determine whether a tool matches category/tag constraints."""
    tool_tags = _tool_searchable_tags(tool)
    if categories and not tool_tags.intersection(categories):
        return False
    return not (tags and not tags.issubset(tool_tags))


def summarize_categories(
    tools: Sequence[Tool],
    *,
    categories: set[str],
    tags: set[str],
    subcategory_mode: bool = False,
) -> list[dict[str, int | str]]:
    """Summarize categories with tool counts."""
    counts: dict[str, int] = {}
    label_fn = (
        _tool_subcategory_from_name if subcategory_mode else _tool_category_from_name
    )

    for tool in tools:
        if not _tool_matches_filters(tool, categories=categories, tags=tags):
            continue
        category = label_fn(tool.name)
        if category is None:
            continue
        counts[category] = counts.get(category, 0) + 1

    return [
        {"category": category, "tool_count": count}
        for category, count in sorted(
            counts.items(), key=lambda item: (-item[1], item[0])
        )
    ]


def render_categories_as_markdown(
    categories: Sequence[dict[str, int | str]],
) -> str:
    """Render category list as compact markdown."""
    if not categories:
        return "No categories matched the query filters."

    lines = ["### Available Categories", "", "**Results**"]
    lines.extend(
        [
            f"- `{row['category']}` ({row['tool_count']} tools)"
            for row in categories
            if isinstance(row.get("category"), str)
            and isinstance(row.get("tool_count"), int)
        ]
    )
    return "\n".join(lines)


def _format_code_list(items: Sequence[str], max_items: int) -> str:
    """Format item names as inline-code list with truncation."""
    shown = list(items[:max_items])
    formatted = ", ".join(f"`{item}`" for item in shown)
    remaining = len(items) - len(shown)
    if remaining > 0:
        return f"{formatted} (+{remaining} more)"
    return formatted


def _resolve_ref_schema(
    schema: dict[str, Any],
    defs: dict[str, Any],
) -> tuple[str | None, dict[str, Any]]:
    """Resolve '#/$defs/Model' references against local schema defs."""
    ref = schema.get("$ref")
    if not isinstance(ref, str) or not ref.startswith("#/$defs/"):
        return None, schema

    model_name = ref.split("/")[-1]
    resolved = defs.get(model_name)
    if isinstance(resolved, dict):
        return model_name, resolved
    return model_name, schema


def _flatten_union_branches(schema: dict[str, Any]) -> list[dict[str, Any]]:
    """Flatten oneOf/anyOf unions into leaf schema branches."""
    branches = schema.get("anyOf") or schema.get("oneOf")
    if not isinstance(branches, list):
        return [schema]

    flattened: list[dict[str, Any]] = []
    for branch in branches:
        if not isinstance(branch, dict):
            continue
        flattened.extend(_flatten_union_branches(branch))
    return flattened or [schema]


def _extract_results_item_schemas(
    output_schema: dict[str, Any],
) -> list[tuple[str | None, dict[str, Any]]]:
    """Extract `results` row schemas from an OpenBB OBBject envelope."""
    properties = output_schema.get("properties")
    if not isinstance(properties, dict):
        return []

    results_schema = properties.get("results")
    if not isinstance(results_schema, dict):
        return []

    defs = output_schema.get("$defs")
    defs = defs if isinstance(defs, dict) else {}

    item_models: list[tuple[str | None, dict[str, Any]]] = []
    for results_branch in _flatten_union_branches(results_schema):
        if results_branch.get("type") != "array":
            continue

        items_schema = results_branch.get("items")
        if not isinstance(items_schema, dict):
            continue

        for item_branch in _flatten_union_branches(items_schema):
            model_name, resolved = _resolve_ref_schema(item_branch, defs)
            if isinstance(resolved, dict):
                item_models.append((model_name, resolved))

    return item_models


def _render_openbb_results_hint(tool: Tool) -> str | None:
    """Render compact OpenBB-specific hints for `results` row shape."""
    output_schema = tool.output_schema
    if not isinstance(output_schema, dict):
        return None

    item_models = _extract_results_item_schemas(output_schema)
    if not item_models:
        return None

    model_names = [name for name, _ in item_models if isinstance(name, str)]
    property_sets: list[set[str]] = []
    dynamic_rows = False
    for _, model_schema in item_models:
        properties = model_schema.get("properties")
        if isinstance(properties, dict) and properties:
            property_sets.append(set(properties.keys()))
            continue

        if (
            isinstance(properties, dict)
            and not properties
            and model_schema.get("additionalProperties") is True
        ):
            dynamic_rows = True

    lines: list[str] = []
    if model_names:
        deduped_models = list(dict.fromkeys(model_names))
        lines.append(
            "- `results` row models: "
            + _format_code_list(deduped_models, OPENBB_HINT_MAX_MODELS)
        )

    if dynamic_rows:
        lines.append(
            "- `results` rows are dynamic objects; keys vary by provider/tool."
        )

    if property_sets:
        common_fields = sorted(set.intersection(*property_sets))
        if common_fields:
            lines.append(
                "- common `results` fields: "
                + _format_code_list(common_fields, OPENBB_HINT_MAX_FIELDS)
            )
        else:
            sample_fields = sorted(next(iter(property_sets)))
            lines.append(
                "- sample `results` fields: "
                + _format_code_list(sample_fields, OPENBB_HINT_MAX_FIELDS)
            )

    if not lines:
        return None
    return "\n".join(lines)


def serialize_openbb_tools_for_output_markdown(tools: Sequence[Tool]) -> str:
    """Serialize tools as markdown + compact OpenBB output-shape hints."""
    if not tools:
        return "No tools matched the query."

    rendered_blocks: list[str] = []
    for tool in tools:
        block = serialize_tools_for_output_markdown([tool]).strip()
        hint = _render_openbb_results_hint(tool)
        if hint:
            block = f"{block}\n\n**OpenBB Result Hints**\n{hint}"
        rendered_blocks.append(block)

    return "\n\n".join(rendered_blocks)


class OpenBBBM25SearchTransform(BM25SearchTransform):
    """BM25 search transform with category/tag filters."""

    def _resolve_max_results(self, requested_max_results: int | None) -> int:
        """Resolve max results using configured cap."""
        if requested_max_results is None:
            return self._max_results
        return max(1, min(requested_max_results, self._max_results))

    async def search_tools(
        self,
        tools: Sequence[Tool],
        query: str,
        *,
        categories: set[str] | None = None,
        tags: set[str] | None = None,
        requested_max_results: int | None = None,
    ) -> Sequence[Tool]:
        """Search tools with optional category/tag filters and per-call max-results override."""
        categories = categories or set()
        tags = tags or set()
        resolved_max_results = self._resolve_max_results(requested_max_results)

        filtered_tools = [
            tool
            for tool in tools
            if _tool_matches_filters(tool, categories=categories, tags=tags)
        ]

        if not filtered_tools:
            return []

        if not query:
            return sorted(filtered_tools, key=lambda tool: tool.name)[
                :resolved_max_results
            ]

        current_hash = _catalog_hash(filtered_tools)
        last_hash = cast(str | None, getattr(self, "_last_hash", None))
        index = cast(_BM25Index, getattr(self, "_index"))
        if current_hash != last_hash:
            documents = [_extract_searchable_text(t) for t in filtered_tools]
            new_index = _BM25Index(index.k1, index.b)
            new_index.build(documents)
            self._index, self._indexed_tools, self._last_hash = (
                new_index,
                filtered_tools,
                current_hash,
            )
            index = new_index

        indexed_tools = cast(Sequence[Tool], getattr(self, "_indexed_tools"))
        indices = index.query(query, resolved_max_results)
        return [indexed_tools[i] for i in indices]

    async def _search(self, tools: Sequence[Tool], query: str) -> Sequence[Tool]:
        """Compatibility override for BaseSearchTransform interface."""
        return await self.search_tools(tools, query)


class OpenBBCodeMode(CodeMode):
    """OpenBB-specific CodeMode wrapper with compact search output."""

    def __init__(
        self,
        *,
        search_max_results: int = 30,
        search_output_format: Literal["json", "markdown"] = "markdown",
        **kwargs: Any,
    ) -> None:
        """Initialize Code Mode with OpenBB-specific search defaults."""
        custom_search_serializer = kwargs.pop("search_result_serializer", None)
        search_transform = kwargs.get("search_transform")
        if search_transform is None:
            kwargs["search_transform"] = OpenBBBM25SearchTransform(
                max_results=search_max_results
            )
        elif search_max_results != 30:
            logger.warning(
                "OpenBBCodeMode: 'search_max_results' is ignored when a custom "
                "'search_transform' is provided."
            )

        super().__init__(**kwargs)
        self._search_output_format = search_output_format
        if custom_search_serializer is not None:
            self._search_result_serializer: SearchResultSerializer = (
                custom_search_serializer
            )
        elif search_output_format == "markdown":
            self._search_result_serializer = serialize_openbb_tools_for_output_markdown
        else:
            self._search_result_serializer = serialize_tools_for_output_json

    async def _render_search_results(self, tools: Sequence[Tool]) -> Any:
        """Render tool search output with configurable serializer."""
        rendered = self._search_result_serializer(tools)
        if inspect.isawaitable(rendered):
            return await rendered
        return rendered

    def _make_search_tool(self) -> Tool:
        transform = self
        output_format = self._search_output_format
        search_transform = self._search_transform
        render_search_results = self._render_search_results

        async def search(
            query: Annotated[
                str,
                "Natural-language text search query.",
            ] = "",
            *,
            category: Annotated[
                str | None,
                "Top-level category filter (e.g. 'equity', 'economy', 'crypto').",
            ] = None,
            subcategory: Annotated[
                str | None,
                "Subcategory filter (e.g. 'price', 'fundamental', 'discovery').",
            ] = None,
            provider: Annotated[
                str | None,
                "Provider filter (e.g. 'intrinio', 'fmp', 'yfinance').",
            ] = None,
            max_results: Annotated[
                int | None,
                "Optional per-query result count. Clamped to the server-configured cap.",
            ] = None,
            list_categories: Annotated[
                bool,
                (
                    "If True, return category counts; when `category` is set, "
                    "return matching subcategory counts."
                ),
            ] = False,
            ctx: Context | None = None,
        ) -> str | list[dict[str, Any]]:
            """Search OpenBB tools or list category/subcategory counts.

            Recommended workflow:
            - Step 1: List categories
              `search(list_categories=True)`
              -> `<category_a> (N tools)`, `<category_b> (N tools)`, ...
            - Step 2: List subcategories in a selected category
              `search(category="<category>", list_categories=True)`
              -> `<subcategory_a> (N tools)`, `<subcategory_b> (N tools)`, ...
            - Step 3: Filter by provider within category + subcategory
              `search(query="<topic>", category="<category>", subcategory="<subcategory>",`
              `provider="<provider>", max_results=20)`

            Optional concrete example:
            - `search(query="fundamental", category="equity",`
              `subcategory="fundamental", provider="yfinance", max_results=20)`

            Notes:
            - Filters are case-insensitive.
            - `subcategory` and `provider` are tag filters and both must match when provided.
            - If no results are returned, try nearby query variants (e.g. singular/plural).
            """
            category_set = {category.strip().lower()} if category else set()
            tag_set: set[str] = set()
            if subcategory:
                normalized_subcategory = subcategory.strip().lower()
                if normalized_subcategory:
                    tag_set.add(normalized_subcategory)
            if provider:
                normalized_provider = provider.strip().lower()
                if normalized_provider:
                    tag_set.add(normalized_provider)

            all_tools = await transform.get_tool_catalog(ctx)

            if list_categories:
                category_rows = summarize_categories(
                    all_tools,
                    categories=category_set,
                    tags=tag_set,
                    subcategory_mode=bool(category_set),
                )
                if output_format == "markdown":
                    return render_categories_as_markdown(category_rows)
                return category_rows

            if isinstance(search_transform, OpenBBBM25SearchTransform):
                results = await search_transform.search_tools(
                    all_tools,
                    query,
                    categories=category_set,
                    tags=tag_set,
                    requested_max_results=max_results,
                )
            else:
                search_fn = getattr(search_transform, "_search")
                results = await search_fn(all_tools, query)
            return await render_search_results(results)

        return Tool.from_function(fn=search, name=self.search_tool_name)
