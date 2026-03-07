"""Tests for tool execution, prompt rendering, and bundled skill integration.

These tests exercise the actual closure-defined tools (discovery and prompt)
and verify that the real bundled skill files render correctly through the
StaticPrompt pipeline.
"""

# pylint: disable=protected-access,unused-argument,import-outside-toplevel

import os
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from mcp.types import TextContent
from openbb_mcp_server.app.app import create_mcp_server
from openbb_mcp_server.models.prompts import StaticPrompt
from openbb_mcp_server.models.settings import MCPSettings

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

SKILLS_DIR = Path(__file__).resolve().parent.parent.parent / (
    "openbb_mcp_server" + os.sep + "skills"
)


def _capture_decorated_tools(mock_mcp_instance):
    """Patch ``mock_mcp_instance.tool`` so the undecorated closures are captured.

    Returns a dict mapping ``func.__name__`` → the original function object.
    """
    decorated: dict[str, object] = {}

    def tool_decorator_factory(*args, **kwargs):
        def decorator(func):
            decorated[func.__name__] = func
            return MagicMock()

        return decorator

    mock_mcp_instance.tool = MagicMock(side_effect=tool_decorator_factory)
    return decorated


def _build_server(
    settings: MCPSettings,
    *,
    prompts_json: list | None = None,
):
    """Construct the MCP server with controlled mocks and return helpers.

    Returns ``(mcp_mock, decorated_functions)``.
    """
    fastapi_app = FastAPI()

    mock_processed_data = MagicMock()
    mock_processed_data.route_lookup = {}
    mock_processed_data.route_maps = []
    mock_processed_data.prompt_definitions = prompts_json or []

    mock_mcp_instance = MagicMock()
    mock_mcp_instance.render_prompt = AsyncMock()

    decorated = _capture_decorated_tools(mock_mcp_instance)

    with (
        patch(
            "openbb_mcp_server.app.app.process_fastapi_routes_for_mcp",
            return_value=mock_processed_data,
        ),
        patch(
            "openbb_mcp_server.app.app.FastMCP.from_fastapi",
            return_value=mock_mcp_instance,
        ),
    ):
        create_mcp_server(settings, fastapi_app)

    return mock_mcp_instance, decorated


# ===================================================================
# PromptsAsTools transform tests
# ===================================================================


class TestTransformsAdded:
    """Tests verifying that PromptsAsTools and ResourcesAsTools transforms are registered."""

    def test_transforms_are_added(self):
        """PromptsAsTools and ResourcesAsTools transforms are always registered."""
        from fastmcp.server.transforms import PromptsAsTools, ResourcesAsTools

        # Disable discovery so only 2 transforms are added
        settings = MCPSettings(enable_tool_discovery=False)  # type: ignore
        mock_mcp, _ = _build_server(settings)

        transforms = [call[0][0] for call in mock_mcp.add_transform.call_args_list]
        transform_types = [type(t) for t in transforms]
        assert PromptsAsTools in transform_types
        assert ResourcesAsTools in transform_types

    def test_discovery_transform_added_when_enabled(self):
        """When enable_tool_discovery=True, a search transform is also added."""

        settings = MCPSettings(enable_tool_discovery=True)  # type: ignore
        mock_mcp, _ = _build_server(settings)

        # At minimum 3 transforms: PromptsAsTools, ResourcesAsTools, search
        assert mock_mcp.add_transform.call_count >= 3

    def test_no_hand_rolled_prompt_or_resource_tools(self):
        """The old list_prompts / execute_prompt / list_resources / read_resource closures are no longer registered."""
        settings = MCPSettings()  # type: ignore
        _, decorated = _build_server(settings)

        assert "list_prompts" not in decorated
        assert "execute_prompt" not in decorated
        assert "list_resources" not in decorated
        assert "read_resource" not in decorated

    def test_inline_prompt_stores_argument_defaults(self):
        """Inline prompt definitions store defaults on StaticPrompt.argument_defaults."""
        prompt_def = {
            "name": "my_prompt",
            "description": "Test",
            "content": "Hello {name}, focus on {aspect}",
            "arguments": [
                {"name": "name", "type": "str", "description": "Name"},
                {
                    "name": "aspect",
                    "type": "str",
                    "description": "Aspect",
                    "default": "fundamentals",
                },
            ],
        }
        settings = MCPSettings()  # type: ignore
        mock_mcp, _ = _build_server(settings, prompts_json=[prompt_def])

        # Find the StaticPrompt among add_prompt calls
        added_prompts = [
            call[0][0]
            for call in mock_mcp.add_prompt.call_args_list
            if isinstance(call[0][0], StaticPrompt)
        ]
        assert len(added_prompts) == 1
        assert added_prompts[0].argument_defaults == {"aspect": "fundamentals"}

    @pytest.mark.asyncio
    async def test_static_prompt_renders_with_defaults(self):
        """StaticPrompt.render() applies argument_defaults when caller omits them."""
        from fastmcp.prompts import PromptArgument

        prompt = StaticPrompt(
            name="greeting",
            content="Hello {name}, focus on {aspect}",
            arguments=[
                PromptArgument(name="name", required=True),
                PromptArgument(name="aspect", required=False),
            ],
            argument_defaults={"aspect": "fundamentals"},
        )

        rendered = await prompt.render(arguments={"name": "AAPL"})
        assert rendered[0].content.text == "Hello AAPL, focus on fundamentals"

    @pytest.mark.asyncio
    async def test_static_prompt_caller_overrides_defaults(self):
        """Caller-supplied values override argument_defaults."""
        from fastmcp.prompts import PromptArgument

        prompt = StaticPrompt(
            name="greeting",
            content="Hello {name}, focus on {aspect}",
            arguments=[
                PromptArgument(name="name", required=True),
                PromptArgument(name="aspect", required=False),
            ],
            argument_defaults={"aspect": "fundamentals"},
        )

        rendered = await prompt.render(
            arguments={"name": "AAPL", "aspect": "technicals"}
        )
        assert rendered[0].content.text == "Hello AAPL, focus on technicals"


# ===================================================================
# Bundled skill rendering tests
# ===================================================================


class TestBundledSkillRendering:
    """Verify each real skill file renders through StaticPrompt without error."""

    EXPECTED_SKILLS = {
        "develop_extension": "Build an OpenBB Platform Extension",
        "build_workspace_app": "Build and Run OpenBB Workspace Applications",
        "configure_mcp_server": "Configure and Build the OpenBB MCP Server",
        "work_with_server": "Working With the OpenBB MCP Server",
    }

    def test_skills_directory_exists(self):
        """Verify the skills directory exists at the expected path."""
        assert SKILLS_DIR.is_dir(), f"Skills directory not found: {SKILLS_DIR}"

    def test_all_expected_skills_present(self):
        """Confirm all expected skill subdirectories with SKILL.md are present."""
        skill_dirs = {
            d.name
            for d in SKILLS_DIR.iterdir()
            if d.is_dir() and (d / "SKILL.md").exists()
        }
        for name in self.EXPECTED_SKILLS:
            assert name in skill_dirs, f"Missing skill subdirectory: {name}/SKILL.md"

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "skill_name,expected_heading",
        list(EXPECTED_SKILLS.items()),
        ids=list(EXPECTED_SKILLS.keys()),
    )
    async def test_skill_renders_without_error(self, skill_name, expected_heading):
        """Each skill file renders to a PromptMessage with full content intact."""
        skill_file = SKILLS_DIR / skill_name / "SKILL.md"
        content = skill_file.read_text(encoding="utf-8")
        assert len(content) > 100, f"Skill {skill_name} seems too short"

        prompt = StaticPrompt(
            name=skill_name,
            description=expected_heading,
            content=content,
            arguments=None,
            tags={"skill"},
        )
        rendered = await prompt.render()

        assert len(rendered) == 1
        assert rendered[0].role == "user"
        assert isinstance(rendered[0].content, TextContent)
        assert rendered[0].content.text == content

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "skill_name",
        list(EXPECTED_SKILLS.keys()),
        ids=list(EXPECTED_SKILLS.keys()),
    )
    async def test_skill_preserves_curly_braces(self, skill_name):
        """Skills with code blocks containing {} must not raise KeyError."""
        skill_file = SKILLS_DIR / skill_name / "SKILL.md"
        content = skill_file.read_text(encoding="utf-8")

        prompt = StaticPrompt(
            name=skill_name,
            description="test",
            content=content,
            arguments=None,
            tags={"skill"},
        )
        # This would raise KeyError if str.format() is incorrectly applied
        rendered = await prompt.render()
        assert rendered[0].content.text == content

    @pytest.mark.asyncio
    async def test_skill_render_with_empty_arguments(self):
        """Passing empty dict as arguments should still bypass str.format."""
        skill_file = SKILLS_DIR / "develop_extension" / "SKILL.md"
        content = skill_file.read_text(encoding="utf-8")

        prompt = StaticPrompt(
            name="develop_extension",
            description="test",
            content=content,
            arguments=None,
            tags={"skill"},
        )
        # Explicit empty dict should also be safe
        rendered = await prompt.render(arguments={})
        assert rendered[0].content.text == content

    def test_skill_description_from_first_heading(self):
        """Verify that each SKILL.md has the expected markdown heading (after YAML frontmatter)."""
        for skill_name, expected_heading in self.EXPECTED_SKILLS.items():
            skill_file = SKILLS_DIR / skill_name / "SKILL.md"
            content = skill_file.read_text(encoding="utf-8")
            # Skip YAML frontmatter block (--- ... ---)
            lines = content.splitlines()
            in_frontmatter = lines[0].strip() == "---" if lines else False
            heading = ""
            for i, line in enumerate(lines):
                if i == 0 and in_frontmatter:
                    continue
                if in_frontmatter and line.strip() == "---":
                    in_frontmatter = False
                    continue
                if not in_frontmatter and line.startswith("#"):
                    heading = line.lstrip("# ").strip()
                    break
            assert (
                heading == expected_heading
            ), f"Skill '{skill_name}' heading mismatch: got '{heading}', expected '{expected_heading}'"


# ===================================================================
# Integration: skills loaded and accessible via prompt tools
# ===================================================================


class TestSkillsIntegration:
    """Test skills loading end-to-end through create_mcp_server."""

    @patch("openbb_mcp_server.app.app.process_fastapi_routes_for_mcp")
    @patch("openbb_mcp_server.app.app.FastMCP.from_fastapi")
    def test_bundled_skills_registered_via_provider(
        self, mock_from_fastapi, mock_process_routes
    ):
        """Bundled skills are registered via mcp.add_provider(SkillsDirectoryProvider)."""
        from fastmcp.server.providers.skills import SkillsDirectoryProvider

        settings = MCPSettings()  # type: ignore  (uses default skills dir)
        fastapi_app = FastAPI()

        mock_processed_data = MagicMock()
        mock_processed_data.route_lookup = {}
        mock_processed_data.route_maps = []
        mock_processed_data.prompt_definitions = []
        mock_process_routes.return_value = mock_processed_data

        mock_mcp_instance = MagicMock()
        mock_from_fastapi.return_value = mock_mcp_instance

        create_mcp_server(settings, fastapi_app)

        provider_calls = mock_mcp_instance.add_provider.call_args_list
        assert len(provider_calls) >= 1
        assert isinstance(provider_calls[0][0][0], SkillsDirectoryProvider)

    @patch("openbb_mcp_server.app.app.process_fastapi_routes_for_mcp")
    @patch("openbb_mcp_server.app.app.FastMCP.from_fastapi")
    def test_skill_md_files_have_content(self, mock_from_fastapi, mock_process_routes):
        """Each bundled SKILL.md file has non-trivial content."""
        for skill_name in [
            "develop_extension",
            "build_workspace_app",
            "configure_mcp_server",
            "work_with_server",
        ]:
            skill_file = SKILLS_DIR / skill_name / "SKILL.md"
            assert skill_file.exists(), f"Missing: {skill_file}"
            content = skill_file.read_text(encoding="utf-8")
            assert (
                len(content) > 500
            ), f"Skill '{skill_name}' SKILL.md is suspiciously short ({len(content)} chars)"

    @patch("openbb_mcp_server.app.app.process_fastapi_routes_for_mcp")
    @patch("openbb_mcp_server.app.app.FastMCP.from_fastapi")
    def test_no_skill_prompts_registered(self, mock_from_fastapi, mock_process_routes):
        """Skills are no longer registered as prompts with the 'skill' tag."""
        settings = MCPSettings()  # type: ignore
        fastapi_app = FastAPI()

        mock_processed_data = MagicMock()
        mock_processed_data.route_lookup = {}
        mock_processed_data.route_maps = []
        mock_processed_data.prompt_definitions = []
        mock_process_routes.return_value = mock_processed_data

        mock_mcp_instance = MagicMock()
        mock_from_fastapi.return_value = mock_mcp_instance

        create_mcp_server(settings, fastapi_app)

        skill_prompt_calls = [
            c
            for c in mock_mcp_instance.add_prompt.call_args_list
            if hasattr(c[0][0], "tags") and "skill" in c[0][0].tags
        ]
        assert (
            skill_prompt_calls == []
        ), "Skills should not be registered as prompts in FastMCP v3 — use add_provider instead"
