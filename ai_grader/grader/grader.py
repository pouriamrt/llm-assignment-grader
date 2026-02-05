"""Grade assignments using LangChain and an LLM (text + images, multimodal)."""

import os
from pathlib import Path
from typing import Any

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from loguru import logger

_SYSTEM_PROMPT = (
    "You are an expert grader. Grade the student's assignment according to the "
    "grading criteria and instructions provided. Be thorough, concise, fair, and constructive. "
    "Provide clear feedback and a grade/score if the instructions ask for one. "
    "When images are included, consider them as part of the submission "
    "(e.g. diagrams, screenshots)."
)


def _get_llm(
    provider: str = "auto",
    model: str | None = None,
    api_key: str | None = None,
):
    """
    Create an LLM instance. Uses OPENAI_API_KEY or ANTHROPIC_API_KEY from env.

    Args:
        provider: "openai", "anthropic", or "auto" (tries OpenAI first, then Anthropic).
        model: Model name (optional; uses defaults if not set).
        api_key: Override API key (optional).
    """
    key = api_key
    if provider == "openai" or (provider == "auto" and not key):
        key = key or os.getenv("OPENAI_API_KEY")
        if key:
            logger.debug("Using OpenAI LLM")
            return ChatOpenAI(
                model=model or "gpt-5.2",
                api_key=key,
                temperature=0,
            )

    if provider == "anthropic" or (provider == "auto" and not key):
        key = key or os.getenv("ANTHROPIC_API_KEY")
        if key:
            logger.debug("Using Anthropic LLM")
            return ChatAnthropic(
                model=model or "claude-sonnet-4-20250514",
                api_key=key,
                temperature=0,
            )

    logger.error("No LLM API key found (OPENAI_API_KEY or ANTHROPIC_API_KEY)")
    raise ValueError(
        "No LLM API key found. Set OPENAI_API_KEY or ANTHROPIC_API_KEY in .env or environment."
    )


def _build_user_content(
    context: str | list[dict[str, Any]], grading_prompt: str
) -> str | list[dict[str, Any]]:
    """Build user message content: string for text-only, list of parts for multimodal."""
    header = f"""## Grading Instructions

{grading_prompt}

---

## Student Submission (all files combined)

"""
    if isinstance(context, list) and context:
        return [{"type": "text", "text": header}, *context]
    return header + (context if isinstance(context, str) else "").strip()


def grade_assignment(
    context: str | list[dict[str, Any]],
    grading_prompt: str,
    *,
    provider: str = "auto",
    model: str | None = None,
) -> str:
    """
    Grade a single assignment using the LLM (supports text and images).

    Args:
        context: Combined content of all submission files: either a string (text only)
            or a list of multimodal content parts (text + image_url) for the LLM.
        grading_prompt: User-defined grading instructions (from markdown).
        provider: "openai", "anthropic", or "auto".
        model: Model name override.

    Returns:
        LLM grading response (text).
    """
    llm = _get_llm(provider=provider, model=model)
    user_content = _build_user_content(context, grading_prompt)
    messages = [
        SystemMessage(content=_SYSTEM_PROMPT),
        HumanMessage(content=user_content),
    ]
    response = llm.invoke(messages)
    return response.content if hasattr(response, "content") else str(response)


async def grade_assignment_async(
    context: str | list[dict[str, Any]],
    grading_prompt: str,
    *,
    provider: str = "auto",
    model: str | None = None,
) -> str:
    """
    Grade a single assignment using the LLM (async; supports text and images).

    Args:
        context: Combined content: string (text only) or list of multimodal parts.
        grading_prompt: User-defined grading instructions (from markdown).
        provider: "openai", "anthropic", or "auto".
        model: Model name override.

    Returns:
        LLM grading response (text).
    """
    llm = _get_llm(provider=provider, model=model)
    user_content = _build_user_content(context, grading_prompt)
    messages = [
        SystemMessage(content=_SYSTEM_PROMPT),
        HumanMessage(content=user_content),
    ]
    response = await llm.ainvoke(messages)
    return response.content if hasattr(response, "content") else str(response)


def load_grading_prompt(prompt_path: Path) -> str:
    """Load grading prompt from a markdown file."""
    return prompt_path.read_text(encoding="utf-8").strip()
