"""Grade assignments using LangChain and an LLM (text + images, multimodal)."""

import os
from pathlib import Path
from typing import Any

import tiktoken
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from loguru import logger

# Conservative context window sizes (input side) for common models; reserve room for output.
_DEFAULT_CONTEXT_WINDOW = 128_000
_CONTEXT_WINDOWS: dict[str, int] = {
    "gpt-4o": 128_000,
    "gpt-4o-mini": 128_000,
    "gpt-4.1": 128_000,
    "gpt-4.1-mini": 128_000,
    "gpt-5.2": 128_000,
    "claude-sonnet-4-20250514": 200_000,
    "claude-sonnet-4-5-20250929": 200_000,
}

# Approximate tokens per image (vision APIs); used when truncating multimodal content.
_ESTIMATE_TOKENS_PER_IMAGE = 1000


def _get_encoding():
    """Cached tiktoken encoding for token counting/truncation."""
    if not hasattr(_get_encoding, "_enc"):
        _get_encoding._enc = tiktoken.get_encoding("cl100k_base")
    return _get_encoding._enc


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


def _get_context_window(model_name: str | None) -> int:
    """Return context window size (input tokens) for the model."""
    if not model_name:
        return _DEFAULT_CONTEXT_WINDOW
    lower = model_name.lower()
    # Match longest key that appears in model name so
    # "gpt-4o-mini" matches "gpt-4o-mini" not "gpt-4o"
    best_key: str | None = None
    for key, size in _CONTEXT_WINDOWS.items():
        if key in lower and (best_key is None or len(key) > len(best_key)):
            best_key = key
    return _CONTEXT_WINDOWS[best_key] if best_key else _DEFAULT_CONTEXT_WINDOW


def _count_text_tokens(text: str) -> int:
    """Count tokens in text using OpenAI's cl100k
    encoding (reasonable for both OpenAI and Anthropic)."""
    try:
        return len(_get_encoding().encode(text))
    except Exception:
        return len(text) // 4  # fallback rough estimate


def _truncate_text_to_tokens(text: str, max_tokens: int) -> str:
    """Truncate text from the end so it has at most max_tokens."""
    if max_tokens <= 0:
        return ""
    try:
        enc = _get_encoding()
        tokens = enc.encode(text)
        if len(tokens) <= max_tokens:
            return text
        truncated = enc.decode(tokens[:max_tokens])
        return truncated.rstrip() + "\n\n[Content truncated due to length limits.]"
    except Exception:
        return text[: max_tokens * 4] + "\n\n[Content truncated due to length limits.]"


def _estimate_user_content_tokens(user_content: str | list[dict[str, Any]]) -> int:
    """Estimate token count of user message content (text + rough image estimate)."""
    if isinstance(user_content, str):
        return _count_text_tokens(user_content)
    total = 0
    for part in user_content:
        if part.get("type") == "text" and part.get("text"):
            total += _count_text_tokens(part["text"])
        elif part.get("type") == "image_url" or part.get("type") == "image":
            total += _ESTIMATE_TOKENS_PER_IMAGE
    return total


def _truncate_user_content(
    user_content: str | list[dict[str, Any]], max_tokens: int
) -> str | list[dict[str, Any]]:
    """Truncate user content to at most max_tokens (from the end);
    preserves header for list form."""
    if max_tokens <= 0:
        return (
            "[Submission truncated: exceeded token limit.]"
            if isinstance(user_content, str)
            else [{"type": "text", "text": "[Submission truncated: exceeded token limit.]"}]
        )
    if isinstance(user_content, str):
        return _truncate_text_to_tokens(user_content, max_tokens)
    # Multimodal: keep parts from the start until we would exceed max_tokens,
    # then truncate last text.
    result: list[dict[str, Any]] = []
    used = 0
    for part in user_content:
        part_tokens = (
            _count_text_tokens(part["text"])
            if part.get("type") == "text" and part.get("text")
            else _ESTIMATE_TOKENS_PER_IMAGE
        )
        if used + part_tokens <= max_tokens:
            result.append(part)
            used += part_tokens
        elif part.get("type") == "text" and part.get("text") and used < max_tokens:
            remaining = max_tokens - used
            truncated_text = _truncate_text_to_tokens(part["text"], remaining)
            result.append({"type": "text", "text": truncated_text})
            used = max_tokens
            break
        else:
            break
    if result and used < max_tokens:
        return result
    if not result:
        return [{"type": "text", "text": "[Submission truncated: exceeded token limit.]"}]
    return result


def _is_context_length_error(exc: BaseException) -> bool:
    """True if the exception indicates context/token length was exceeded."""
    msg = (getattr(exc, "message", None) or str(exc)).lower()
    return "context" in msg and ("length" in msg or "limit" in msg or "exceeded" in msg)


def _apply_truncation_and_invoke(
    llm: Any,
    full_user_content: str | list[dict[str, Any]],
    reserve_tokens: int = 4096,
    max_retries_on_length: int = 2,
) -> str:
    """Build messages, truncate if over context limit,
    invoke with retry on context-length errors."""
    model_name = getattr(llm, "model_name", None) or getattr(llm, "model", None)
    model_name = model_name if isinstance(model_name, str) else None
    context_window = _get_context_window(model_name)

    system_msg = SystemMessage(content=_SYSTEM_PROMPT)
    get_num_tokens = getattr(llm, "get_num_tokens_from_messages", None)
    if not callable(get_num_tokens):
        get_num_tokens = None

    max_user_tokens = context_window - reserve_tokens
    if get_num_tokens is not None:
        try:
            system_tokens = get_num_tokens([system_msg])
            max_user_tokens = context_window - reserve_tokens - system_tokens
        except Exception:
            pass

    last_exc: BaseException | None = None
    for attempt in range(max_retries_on_length + 1):
        # Truncate more aggressively on each retry after a context-length error
        if attempt == 0:
            cap = max_user_tokens
        else:
            cap = max(1024, max_user_tokens // (2**attempt))
        user_content = _truncate_user_content(full_user_content, cap)
        if attempt > 0:
            logger.warning(
                "Retrying with truncated content (attempt {}), max_user_tokens≈{}",
                attempt + 1,
                cap,
            )
        messages = [system_msg, HumanMessage(content=user_content)]
        try:
            response = llm.invoke(messages)
            return response.content if hasattr(response, "content") else str(response)
        except BaseException as e:
            last_exc = e
            if _is_context_length_error(e) and attempt < max_retries_on_length:
                logger.warning("Context length exceeded, truncating and retrying: {}", e)
                continue
            raise
    if last_exc is not None:
        raise last_exc
    raise RuntimeError("Unexpected truncation/retry loop exit")


async def _apply_truncation_and_ainvoke(
    llm: Any,
    full_user_content: str | list[dict[str, Any]],
    reserve_tokens: int = 4096,
    max_retries_on_length: int = 2,
) -> str:
    """Build messages, truncate if over context limit,
    ainvoke with retry on context-length errors."""
    model_name = getattr(llm, "model_name", None) or getattr(llm, "model", None)
    model_name = model_name if isinstance(model_name, str) else None
    context_window = _get_context_window(model_name)

    system_msg = SystemMessage(content=_SYSTEM_PROMPT)
    get_num_tokens = getattr(llm, "get_num_tokens_from_messages", None)
    if not callable(get_num_tokens):
        get_num_tokens = None

    max_user_tokens = context_window - reserve_tokens
    if get_num_tokens is not None:
        try:
            system_tokens = get_num_tokens([system_msg])
            max_user_tokens = context_window - reserve_tokens - system_tokens
        except Exception:
            pass

    last_exc: BaseException | None = None
    for attempt in range(max_retries_on_length + 1):
        if attempt == 0:
            cap = max_user_tokens
        else:
            cap = max(1024, max_user_tokens // (2**attempt))
        user_content = _truncate_user_content(full_user_content, cap)
        if attempt > 0:
            logger.warning(
                "Retrying with truncated content (attempt {}), max_user_tokens≈{}",
                attempt + 1,
                cap,
            )
        messages = [system_msg, HumanMessage(content=user_content)]
        try:
            response = await llm.ainvoke(messages)
            return response.content if hasattr(response, "content") else str(response)
        except BaseException as e:
            last_exc = e
            if _is_context_length_error(e) and attempt < max_retries_on_length:
                logger.warning("Context length exceeded, truncating and retrying: {}", e)
                continue
            raise
    if last_exc is not None:
        raise last_exc
    raise RuntimeError("Unexpected truncation/retry loop exit")


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
    full_user_content = _build_user_content(context, grading_prompt)
    return _apply_truncation_and_invoke(llm, full_user_content)


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
    full_user_content = _build_user_content(context, grading_prompt)
    return await _apply_truncation_and_ainvoke(llm, full_user_content)


def load_grading_prompt(prompt_path: Path) -> str:
    """Load grading prompt from a markdown file."""
    return prompt_path.read_text(encoding="utf-8").strip()
