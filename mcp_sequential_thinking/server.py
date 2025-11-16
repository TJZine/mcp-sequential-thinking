import json
import re
import os
import sys
from typing import Any, Dict, List, Optional, Union

from mcp.server.fastmcp import FastMCP, Context
from mcp.server.fastmcp.prompts import base

# Use absolute imports when running as a script
try:
    # When installed as a package
    from .models import RiskLevel, ThoughtData, ThoughtStage
    from .storage import ThoughtStorage
    from .analysis import ThoughtAnalyzer
    from .logging_conf import configure_logging
except ImportError:
    # When run directly
    from mcp_sequential_thinking.models import RiskLevel, ThoughtData, ThoughtStage
    from mcp_sequential_thinking.storage import ThoughtStorage
    from mcp_sequential_thinking.analysis import ThoughtAnalyzer
    from mcp_sequential_thinking.logging_conf import configure_logging

logger = configure_logging("sequential-thinking.server")


mcp = FastMCP("sequential-thinking")

storage_dir = os.environ.get("MCP_STORAGE_DIR", None)
storage = ThoughtStorage(storage_dir)

LEGACY_ALIASES = {
    "thought_number": ["thoughtNumber"],
    "total_thoughts": ["totalThoughts"],
    "next_thought_needed": ["nextThoughtNeeded"],
    "tags": ["tags"],
    "axioms_used": ["axiomsUsed"],
    "assumptions_challenged": ["assumptionsChallenged"],
    "files_touched": ["filesTouched"],
    "tests_to_run": ["testsToRun"],
    "dependencies": ["dependencies"],
    "risk_level": ["riskLevel"],
    "confidence_score": ["confidenceScore"],
    "project_id": ["projectId"],
}


def _resolve_legacy_value(
    current_value: Optional[Any],
    legacy_payload: Dict[str, Any],
    target_key: str,
) -> Optional[Any]:
    """Return the first non-None value from current or legacy aliases."""
    if current_value is not None:
        return current_value

    for alias in LEGACY_ALIASES.get(target_key, []):
        if alias in legacy_payload:
            return legacy_payload.pop(alias)
    return None


def _parse_bool(value: Any) -> Optional[bool]:
    """Parse a boolean from incoming tool-bridge values.

    Accepts real bools, and common string forms like "true", "false", "1", "0", "yes", "no".
    Returns None if the value is missing or cannot be parsed.
    """
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, (int,)):
        return bool(value)
    if isinstance(value, str):
        s = value.strip().lower()
        if s in {"true", "1", "yes", "y"}:
            return True
        if s in {"false", "0", "no", "n"}:
            return False
    return None


def _parse_int(value: Any) -> Optional[int]:
    """Parse an int from incoming values (supports numeric strings)."""
    if value is None:
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        v = value.strip()
        if v.isdigit() or (v.startswith("-") and v[1:].isdigit()):
            try:
                return int(v)
            except ValueError:
                return None
    return None


def _parse_list(value: Any) -> Optional[List[str]]:
    """Parse a list of strings from various representations used by clients.

    Supports:
    - list[str]
    - JSON-encoded list in a string
    - Comma/semicolon-separated strings
    Returns None if value is None; otherwise returns a list (possibly empty).
    """
    if value is None:
        return None
    if isinstance(value, list):
        return [str(x) for x in value]
    if isinstance(value, str):
        s = value.strip()
        # Try JSON first
        try:
            parsed = json.loads(s)
            if isinstance(parsed, list):
                return [str(x) for x in parsed]
        except Exception:
            pass
        # Fallback: split by comma or semicolon
        parts = [p.strip() for p in re.split(r"[,;]", s) if p.strip()]
        return parts
    return [str(value)]


@mcp.tool()
def process_thought(
    thought: str,
    thought_number: Optional[Union[int, str]] = None,
    total_thoughts: Optional[Union[int, str]] = None,
    next_thought_needed: Optional[Union[bool, str, int]] = None,
    stage: str = "",
    tags: Optional[Union[List[str], str]] = None,
    axioms_used: Optional[Union[List[str], str]] = None,
    assumptions_challenged: Optional[Union[List[str], str]] = None,
    files_touched: Optional[Union[List[str], str]] = None,
    tests_to_run: Optional[Union[List[str], str]] = None,
    dependencies: Optional[Union[List[str], str]] = None,
    risk_level: Optional[str] = None,
    confidence_score: Optional[Union[float, str]] = None,
    project_id: Optional[str] = None,
    ctx: Optional[Context] = None,
    legacy_kwargs: Optional[Union[Dict[str, Any], str]] = None,
    extra_kwargs: Optional[Union[Dict[str, Any], str]] = None,
    **kwargs,
) -> dict:
    """Add a sequential thought with its metadata.

    Args:
        thought: The content of the thought
        thought_number: The sequence number of this thought
        total_thoughts: The total expected thoughts in the sequence
        next_thought_needed: Whether more thoughts are needed after this one
        stage: The thinking stage (Scoping, Research & Spike, Implementation, Testing, Review)
        tags: Optional keywords or categories for the thought
        axioms_used: Optional list of principles or axioms used in this thought
        assumptions_challenged: Optional list of assumptions challenged by this thought
        files_touched: Optional list of files touched while executing this thought
        tests_to_run: Optional list of tests to run after the thought
        dependencies: Optional list of dependencies or external constraints
        risk_level: Optional risk level ("low", "medium", "high")
        confidence_score: Optional confidence score between 0 and 1
        project_id: Optional identifier for the active project/session
        ctx: Optional MCP context object
        legacy_kwargs: Optional camelCase payload (dict or JSON string)
        extra_kwargs: Optional second legacy payload (dict or JSON string)

    Returns:
        dict: Analysis of the processed thought
    """
    try:
        # Log the request
        logger.info(f"Processing thought #{thought_number}/{total_thoughts} in stage '{stage}'")

        # Normalize legacy/camelCase payloads before validation.
        # Merge explicit legacy_kwargs (which Codex may pass as a JSON string)
        # with any extra unexpected kwargs into a single legacy_payload.
        legacy_payload: Dict[str, Any] = {}

        def _merge_payload(source: Optional[Union[Dict[str, Any], str]]) -> None:
            if source is None:
                return
            if isinstance(source, str):
                try:
                    parsed = json.loads(source)
                except Exception:
                    return
                if isinstance(parsed, dict):
                    legacy_payload.update(parsed)
            elif isinstance(source, dict):
                legacy_payload.update(source)

        _merge_payload(legacy_kwargs)
        _merge_payload(extra_kwargs)
        if kwargs:
            legacy_payload.update(kwargs)

        thought_number = _resolve_legacy_value(thought_number, legacy_payload, "thought_number")
        total_thoughts = _resolve_legacy_value(total_thoughts, legacy_payload, "total_thoughts")
        next_thought_needed = _resolve_legacy_value(next_thought_needed, legacy_payload, "next_thought_needed")
        tags = _resolve_legacy_value(tags, legacy_payload, "tags")
        axioms_used = _resolve_legacy_value(axioms_used, legacy_payload, "axioms_used")
        assumptions_challenged = _resolve_legacy_value(assumptions_challenged, legacy_payload, "assumptions_challenged")
        files_touched = _resolve_legacy_value(files_touched, legacy_payload, "files_touched")
        tests_to_run = _resolve_legacy_value(tests_to_run, legacy_payload, "tests_to_run")
        dependencies = _resolve_legacy_value(dependencies, legacy_payload, "dependencies")
        risk_level = _resolve_legacy_value(risk_level, legacy_payload, "risk_level")
        confidence_score = _resolve_legacy_value(confidence_score, legacy_payload, "confidence_score")
        project_id = _resolve_legacy_value(project_id, legacy_payload, "project_id")

        # Coerce basic types that may arrive as strings from the tool bridge
        tni = _parse_int(thought_number)
        if tni is not None:
            thought_number = tni
        tti = _parse_int(total_thoughts)
        if tti is not None:
            total_thoughts = tti
        ntn = _parse_bool(next_thought_needed)
        if ntn is not None:
            next_thought_needed = ntn
        if isinstance(confidence_score, str):
            try:
                confidence_score = float(confidence_score.strip())
            except Exception:
                confidence_score = None
        # Normalize list-like fields
        tags = _parse_list(tags) or []
        axioms_used = _parse_list(axioms_used) or []
        assumptions_challenged = _parse_list(assumptions_challenged) or []
        files_touched = _parse_list(files_touched) or []
        tests_to_run = _parse_list(tests_to_run) or []
        dependencies = _parse_list(dependencies) or []

        if thought_number is None:
            raise ValueError("thought_number is required")
        if total_thoughts is None:
            raise ValueError("total_thoughts is required")
        if next_thought_needed is None:
            raise ValueError("next_thought_needed is required")

        # Report progress if context is available
        if ctx:
            ctx.report_progress(thought_number - 1, total_thoughts)

        if project_id:
            storage.set_default_project(project_id)

        # Convert stage string to enum (accepts aliases like "Planning")
        thought_stage = ThoughtStage.from_string(stage)
        if risk_level:
            try:
                risk_value = RiskLevel(risk_level.lower())
            except ValueError as exc:
                valid = ", ".join(level.value for level in RiskLevel)
                raise ValueError(f"Invalid risk_level '{risk_level}'. Choose from: {valid}") from exc
        else:
            risk_value = RiskLevel.MEDIUM

        # Create thought data object with defaults for optional fields
        thought_data = ThoughtData(
            thought=thought,
            thought_number=thought_number,
            total_thoughts=total_thoughts,
            next_thought_needed=next_thought_needed,
            stage=thought_stage,
            tags=tags or [],
            axioms_used=axioms_used or [],
            assumptions_challenged=assumptions_challenged or [],
            files_touched=files_touched or [],
            tests_to_run=tests_to_run or [],
            dependencies=dependencies or [],
            risk_level=risk_value,
            confidence_score=confidence_score if confidence_score is not None else 0.5,
        )

        # Validate and store
        thought_data.validate()
        storage.add_thought(thought_data, project_id=project_id)

        # Get all thoughts for analysis
        all_thoughts = storage.get_all_thoughts(project_id=project_id)

        # Analyze the thought
        analysis = ThoughtAnalyzer.analyze_thought(thought_data, all_thoughts)

        # Log success
        logger.info(f"Successfully processed thought #{thought_number}")

        return analysis
    except json.JSONDecodeError as e:
        # Log JSON parsing error
        logger.error(f"JSON parsing error: {e}")
        return {
            "error": f"JSON parsing error: {str(e)}",
            "status": "failed"
        }
    except Exception as e:
        # Log error
        logger.error(f"Error processing thought: {str(e)}")

        return {
            "error": str(e),
            "status": "failed"
        }

@mcp.tool()
def generate_summary(project_id: Optional[str] = None) -> dict:
    """Generate a summary of the entire thinking process.

    Returns:
        dict: Summary of the thinking process
    """
    try:
        logger.info("Generating thinking process summary")

        # Get all thoughts
        all_thoughts = storage.get_all_thoughts(project_id=project_id)

        # Generate summary
        return ThoughtAnalyzer.generate_summary(all_thoughts)
    except json.JSONDecodeError as e:
        logger.error(f"JSON parsing error: {e}")
        return {
            "error": f"JSON parsing error: {str(e)}",
            "status": "failed"
        }
    except Exception as e:
        logger.error(f"Error generating summary: {str(e)}")
        return {
            "error": str(e),
            "status": "failed"
        }

@mcp.tool()
def clear_history(project_id: Optional[str] = None) -> dict:
    """Clear the thought history.

    Returns:
        dict: Status message
    """
    try:
        logger.info("Clearing thought history")
        storage.clear_history(project_id=project_id)
        return {"status": "success", "message": "Thought history cleared"}
    except json.JSONDecodeError as e:
        logger.error(f"JSON parsing error: {e}")
        return {
            "error": f"JSON parsing error: {str(e)}",
            "status": "failed"
        }
    except Exception as e:
        logger.error(f"Error clearing history: {str(e)}")
        return {
            "error": str(e),
            "status": "failed"
        }

@mcp.tool()
def export_session(file_path: str, project_id: Optional[str] = None) -> dict:
    """Export the current thinking session to a file.

    Args:
        file_path: Path to save the exported session

    Returns:
        dict: Status message
    """
    try:
        logger.info(f"Exporting session to {file_path}")
        storage.export_session(file_path, project_id=project_id)
        return {
            "status": "success",
            "message": f"Session exported to {file_path}"
        }
    except json.JSONDecodeError as e:
        logger.error(f"JSON parsing error: {e}")
        return {
            "error": f"JSON parsing error: {str(e)}",
            "status": "failed"
        }
    except Exception as e:
        logger.error(f"Error exporting session: {str(e)}")
        return {
            "error": str(e),
            "status": "failed"
        }

@mcp.tool()
def import_session(file_path: str, project_id: Optional[str] = None) -> dict:
    """Import a thinking session from a file.

    Args:
        file_path: Path to the file to import

    Returns:
        dict: Status message
    """
    try:
        logger.info(f"Importing session from {file_path}")
        storage.import_session(file_path, project_id=project_id)
        return {
            "status": "success",
            "message": f"Session imported from {file_path}"
        }
    except json.JSONDecodeError as e:
        logger.error(f"JSON parsing error: {e}")
        return {
            "error": f"JSON parsing error: {str(e)}",
            "status": "failed"
        }
    except Exception as e:
        logger.error(f"Error importing session: {str(e)}")
        return {
            "error": str(e),
            "status": "failed"
        }


def main():
    """Entry point for the MCP server."""
    logger.info("Starting Sequential Thinking MCP server")

    # Ensure UTF-8 encoding for stdin/stdout
    if hasattr(sys.stdout, 'buffer') and sys.stdout.encoding != 'utf-8':
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', line_buffering=True)
    if hasattr(sys.stdin, 'buffer') and sys.stdin.encoding != 'utf-8':
        import io
        sys.stdin = io.TextIOWrapper(sys.stdin.buffer, encoding='utf-8', line_buffering=True)

    # Flush stdout to ensure no buffered content remains
    sys.stdout.flush()

    # Run the MCP server
    mcp.run()


if __name__ == "__main__":
    # When running the script directly, ensure we're in the right directory
    import os
    import sys

    # Add the parent directory to sys.path if needed
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)

    # Print debug information
    logger.info(f"Python version: {sys.version}")
    logger.info(f"Current working directory: {os.getcwd()}")
    logger.info(f"Script directory: {os.path.dirname(os.path.abspath(__file__))}")
    logger.info(f"Parent directory added to path: {parent_dir}")

    # Run the server
    main()


# === Stage-specific prompts ==================================================


@mcp.prompt()
def scoping_prompt(problem_statement: str, constraints: Optional[str] = None) -> List[base.Message]:
    """Prompt that keeps scoping thoughts grounded."""
    return [
        base.SystemMessage(
            "You are a planning assistant who ensures coding work starts with a clear scope, "
            "definition of done, and success metrics."
        ),
        base.UserMessage(
            "Problem Statement:\n"
            f"{problem_statement}\n\n"
            f"Known constraints: {constraints or 'n/a'}\n"
            "Clarify:\n"
            "1. Desired outcome and non-goals.\n"
            "2. Risks or unknowns that require spikes.\n"
            "3. Metrics or signals that prove the work is finished."
        ),
    ]


@mcp.prompt()
def research_prompt(
    hypothesis: str, repo_context: Optional[str] = None, blocking_dependencies: Optional[str] = None
) -> List[base.Message]:
    """Prompt that accelerates research/spike stages."""
    return [
        base.SystemMessage(
            "You are a technical researcher providing lightweight spikes and references "
            "before implementation begins."
        ),
        base.UserMessage(
            f"Hypothesis/Question:\n{hypothesis}\n\n"
            f"Repo context: {repo_context or 'not provided'}\n"
            f"Known blockers/dependencies: {blocking_dependencies or 'none'}\n"
            "Respond with:\n"
            "- Key docs or code paths to inspect\n"
            "- Proof-of-concept notes or pseudocode\n"
            "- Open questions to answer before coding"
        ),
    ]


@mcp.prompt()
def implementation_prompt(
    plan_outline: str, files_targeted: Optional[List[str]] = None, risk_level: Optional[str] = None
) -> List[base.Message]:
    """Prompt focused on implementation planning."""
    targeted = ", ".join(files_targeted or ["not specified"])
    return [
        base.SystemMessage("You help Codex map implementation steps into sequenced commits."),
        base.UserMessage(
            "Implementation outline:\n"
            f"{plan_outline}\n\n"
            f"Files/areas targeted: {targeted}\n"
            f"Risk level: {risk_level or 'medium'}\n"
            "Return:\n"
            "- Ordered sub-tasks with owners/LLM tools\n"
            "- Tests to run at the end\n"
            "- Instrumentation/logging hooks if risk is high"
        ),
    ]


@mcp.prompt()
def testing_prompt(
    feature_summary: str, tests_to_run: Optional[List[str]] = None, risk_level: Optional[str] = None
) -> List[base.Message]:
    """Prompt to ensure testing thoughts remain thorough."""
    planned_tests = ", ".join(tests_to_run or ["derive from implementation diff"])
    return [
        base.SystemMessage("You are a test strategist ensuring coverage for recent changes."),
        base.UserMessage(
            "Feature summary:\n"
            f"{feature_summary}\n\n"
            f"Planned tests: {planned_tests}\n"
            f"Risk level: {risk_level or 'medium'}\n"
            "Deliver:\n"
            "- Targeted unit/integration tests to execute now\n"
            "- Regression areas to watch\n"
            "- Data or fixtures needed for reproduction"
        ),
    ]


@mcp.prompt()
def review_prompt(
    diff_summary: str, confidence_score: Optional[float] = None, follow_up_items: Optional[str] = None
) -> List[base.Message]:
    """Prompt that helps finalize the review stage."""
    return [
        base.SystemMessage("You conduct code reviews and bake in lessons for future Codex runs."),
        base.UserMessage(
            "Diff summary:\n"
            f"{diff_summary}\n\n"
            f"Confidence score: {confidence_score if confidence_score is not None else 0.5}\n"
            f"Follow-up items: {follow_up_items or 'none logged'}\n"
            "Summarize:\n"
            "- Checklist for reviewers (tests, docs, migration notes)\n"
            "- Items to carry into the next iteration (tech debt, monitoring)\n"
            "- Final go/no-go recommendation"
        ),
    ]
