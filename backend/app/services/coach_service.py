from typing import List, Optional
from typing import Any
from ..config import settings
from ..models.schemas import CoachMessage
from .ollama_client import chat as ollama_chat

try:
    import openai
except Exception:
    openai = None

# If configured, prefer a local mock for offline testing
if settings.use_local_llm_mock:
    try:
        from . import llm_mock as openai  # type: ignore
    except Exception:
        pass

try:
    import httpx
except Exception:
    httpx = None


COACH_SYSTEM_PROMPT = """You are an expert Principal Software Engineer and code review assistant. 
Your role is to help developers understand code changes, assess their impact, and prepare thoughtful review feedback.

You provide:
- Clear explanations of what changed and why it matters
- Architectural impact analysis
- Risk assessment and mitigation suggestions
- Guidance on review priorities and focus areas
- Suggested comments and discussion points for the author

Be concise, professional, and focused on helping the reviewer make informed decisions.
When relevant, reference the code diff context provided."""


async def get_coach_response(
    message: str,
    intent: Optional[str] = None,
    repo: Optional[str] = None,
    conversation_history: List[CoachMessage] = None,
) -> Optional[str]:
    """Get a response from the AI coach based on user message and context."""

    def _extract_text_from_gemini_response(data: dict[str, Any]) -> str | None:
        candidates = data.get("candidates", [])
        if not candidates:
            return None
        parts = candidates[0].get("content", {}).get("parts", [])
        text = "".join(part.get("text", "") for part in parts if isinstance(part, dict)).strip()
        return text or None

    def local_coach_response() -> str:
        normalized = message.strip().lower()

        context_lines = []
        if repo:
            context_lines.append(f"Repository: {repo}")
        if intent:
            context_lines.append(f"Intent: {intent}")

        context_block = ""
        if context_lines:
            context_block = "Context:\n- " + "\n- ".join(context_lines) + "\n\n"

        if any(term in normalized for term in ["first", "priority", "review first"]):
            return (
                f"{context_block}Start with the highest-risk review pass:\n"
                "1. Validate data boundaries and input validation changes.\n"
                "2. Check behavior changes in public interfaces and error paths.\n"
                "3. Confirm tests cover edge cases and regressions.\n"
                "4. Look for hidden coupling across modules before approving."
            )

        if any(term in normalized for term in ["regression", "risky", "risk"]):
            return (
                f"{context_block}Potential regression hotspots:\n"
                "- Shared utility functions or schema/model changes.\n"
                "- Error handling branches and default values.\n"
                "- Callers that rely on previous function signatures or return shapes.\n"
                "Quick check: run unit tests first, then target impacted integration paths."
            )

        if any(term in normalized for term in ["comment", "feedback", "author"]):
            return (
                f"{context_block}Draft review comment:\n"
                "\"I like the direction here. Could we add a focused test for the new edge case and "
                "clarify the failure behavior in the function docstring? That will make the change safer "
                "for future refactors.\""
            )

        return (
            f"{context_block}Good review checklist:\n"
            "- Confirm intent and expected behavior change.\n"
            "- Review correctness, edge cases, and rollback safety.\n"
            "- Check readability and maintainability impact.\n"
            "- Verify test coverage for happy path and failure path.\n"
            "If you share a specific diff section, I can help with a targeted review plan."
        )
    
    # If a local mock was requested at runtime, prefer it
    global openai
    if settings.use_local_llm_mock:
        try:
            from . import llm_mock as _mock
            openai = _mock  # type: ignore
        except Exception:
            pass

    if settings.use_llm and settings.llm_provider in ("ollama", "auto") and httpx:
        messages = []
        if intent or repo:
            context = "Current review context:\n"
            if intent:
                context += f"- Intent: {intent}\n"
            if repo:
                context += f"- Repository: {repo}\n"
            messages.append({"role": "user", "content": context})

        if conversation_history:
            for msg in conversation_history:
                messages.append({"role": msg.role, "content": msg.content})

        messages.append({"role": "user", "content": message})

        prompt_text = [COACH_SYSTEM_PROMPT]
        for msg in messages:
            prompt_text.append(f"{msg['role'].upper()}: {msg['content']}")

        try:
            text = await ollama_chat(
                base_url=settings.ollama_base_url,
                model=settings.ollama_model,
                messages=[
                    {"role": "system", "content": COACH_SYSTEM_PROMPT},
                    {"role": "user", "content": "\n\n".join(prompt_text)},
                ],
                temperature=0.7,
                timeout=120.0,
            )
            if text:
                return text
        except Exception as e:
            print(f"Ollama coach error: {e}")

    if settings.llm_provider == "gemini" and settings.gemini_api_key and httpx:
        messages = []
        if intent or repo:
            context = "Current review context:\n"
            if intent:
                context += f"- Intent: {intent}\n"
            if repo:
                context += f"- Repository: {repo}\n"
            messages.append({"role": "user", "content": context})

        if conversation_history:
            for msg in conversation_history:
                messages.append({"role": msg.role, "content": msg.content})

        messages.append({"role": "user", "content": message})

        prompt_text = [COACH_SYSTEM_PROMPT]
        for msg in messages:
            prompt_text.append(f"{msg['role'].upper()}: {msg['content']}")

        try:
            async with httpx.AsyncClient(timeout=45.0) as client:
                for model_name in [settings.gemini_model, "gemini-2.0-flash-lite", "gemini-1.5-flash"]:
                    if not model_name:
                        continue

                    url = (
                        f"https://generativelanguage.googleapis.com/v1beta/models/"
                        f"{model_name}:generateContent?key={settings.gemini_api_key}"
                    )
                    payload = {
                        "contents": [{"role": "user", "parts": [{"text": "\n\n".join(prompt_text)}]}],
                        "generationConfig": {
                            "temperature": 0.7,
                            "maxOutputTokens": 800,
                        },
                    }

                    response = await client.post(url, json=payload)
                    if response.status_code == 429:
                        continue
                    response.raise_for_status()
                    text = _extract_text_from_gemini_response(response.json())
                    if text:
                        return text
        except Exception as e:
            print(f"Gemini coach error: {e}")

    if not openai or (not settings.openai_api_key and not settings.use_local_llm_mock):
        # Always provide a useful local coaching response when remote LLM is unavailable.
        return local_coach_response()

    # Set the API key if real OpenAI
    try:
        openai.api_key = settings.openai_api_key
    except Exception:
        pass

    # Build conversation context
    messages = [{"role": "system", "content": COACH_SYSTEM_PROMPT}]
    
    # Add context about the current review if available
    if intent or repo:
        context = "Current review context:\n"
        if intent:
            context += f"- Intent: {intent}\n"
        if repo:
            context += f"- Repository: {repo}\n"
        messages.append({"role": "system", "content": context})
    
    # Add conversation history
    if conversation_history:
        for msg in conversation_history:
            messages.append({"role": msg.role, "content": msg.content})
    
    # Add the current user message
    messages.append({"role": "user", "content": message})

    try:
        # OpenAI <=0.x style and local mock compatibility.
        if hasattr(openai, "ChatCompletion"):
            response = openai.ChatCompletion.create(
                model=getattr(settings, "llm_model", "gpt-4o-mini"),
                messages=messages,
                temperature=0.7,
                max_tokens=500,
            )
            if hasattr(response, "choices") and len(response.choices) > 0:
                return response.choices[0].message.content

        # OpenAI >=1.x style.
        if hasattr(openai, "OpenAI"):
            client = openai.OpenAI(api_key=settings.openai_api_key)
            response = client.chat.completions.create(
                model=getattr(settings, "llm_model", "gpt-4o-mini"),
                messages=messages,
                temperature=0.7,
                max_tokens=500,
            )
            if response.choices:
                return response.choices[0].message.content

        return local_coach_response()
    except Exception as e:
        print(f"Error calling LLM: {e}")
        return local_coach_response()
