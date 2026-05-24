from typing import List
import asyncio
import json
from typing import Any
import re
from ..config import settings

from ..models.schemas import AnalyzeDiffResponse, Summary, RoadmapItem, ArchitecturalDrift
from .git_parser import parse_diff
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
    import jsonschema
    from jsonschema import Draft7Validator
except Exception:
    jsonschema = None

try:
    import httpx
except Exception:
    httpx = None


_LLM_PROMPT = '''You are an expert Principal Software Engineer. Given a git diff, produce a JSON object that matches this schema exactly: {"summary": {"intent": str, "cognitive_load_score": "Low|Medium|High", "total_impacted_modules": int}, "review_roadmap": [{"file_path": str, "review_priority": int, "change_type": str, "architectural_impact": str|null, "risk_flags": [str]}], "architectural_drift": {"violates_patterns": bool, "explanation": str|null}}.

Be concise. Return only valid JSON and nothing else (no markdown, no commentary).

If the diff contains hardcoded secrets, API keys, tokens, passwords, private keys, or cloud credentials, flag that as a critical security issue with the strongest priority and explain the exposure clearly.
'''


JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "summary": {
            "type": "object",
            "properties": {
                "intent": {"type": "string"},
                "cognitive_load_score": {"type": "string", "enum": ["Low", "Medium", "High"]},
                "total_impacted_modules": {"type": "integer"},
            },
            "required": ["intent", "cognitive_load_score", "total_impacted_modules"],
        },
        "review_roadmap": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "file_path": {"type": "string"},
                    "review_priority": {"type": "integer"},
                    "change_type": {"type": "string"},
                    "architectural_impact": {"anyOf": [{"type": "string"}, {"type": "null"}]},
                    "risk_flags": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["file_path", "review_priority", "change_type", "risk_flags"],
            },
        },
        "architectural_drift": {
            "type": "object",
            "properties": {
                "violates_patterns": {"type": "boolean"},
                "explanation": {"anyOf": [{"type": "string"}, {"type": "null"}]},
            },
            "required": ["violates_patterns"],
        },
    },
    "required": ["summary", "review_roadmap", "architectural_drift"],
}


def _validate_json_struct(data: dict) -> List[str]:
    if not jsonschema:
        return []
    validator = Draft7Validator(JSON_SCHEMA)
    errors = []
    for e in sorted(validator.iter_errors(data), key=lambda x: x.path):
        path = ".".join([str(p) for p in e.absolute_path]) or "root"
        errors.append(f"{path}: {e.message}")
    return errors


def _extract_json_payload(text: str) -> dict[str, Any]:
    start = text.find("{")
    if start != -1:
        text = text[start:]
    return json.loads(text)


def _build_secret_exposure_response(diff_text: str) -> AnalyzeDiffResponse | None:
    secret_patterns = [
        r"AKIA[0-9A-Z]{12,}",
        r"ASIA[0-9A-Z]{12,}",
        r"(?i)aws_secret_access_key\s*=\s*[\"'][^\"']+[\"']",
        r"(?i)aws_access_key_id\s*=\s*[\"'][^\"']+[\"']",
        r"(?i)secret_access_key\s*=\s*[\"'][^\"']+[\"']",
        r"(?i)access_key_id\s*=\s*[\"'][^\"']+[\"']",
        r"(?i)private_key\s*=\s*[\"'][^\"']+[\"']",
        r"(?i)password\s*=\s*[\"'][^\"']+[\"']",
        r"(?i)token\s*=\s*[\"'][^\"']+[\"']",
    ]

    if not any(re.search(pattern, diff_text) for pattern in secret_patterns):
        return None

    files = parse_diff(diff_text)
    if not files:
        return None

    file_path = files[0]["file_path"]
    summary = Summary(
        intent="Detect hardcoded secrets and credential exposure",
        cognitive_load_score="High",
        total_impacted_modules=len(files),
    )

    review_roadmap = [
        RoadmapItem(
            file_path=file_path,
            review_priority=1,
            change_type=files[0].get("change_type", "Modified"),
            architectural_impact="Hardcoded credentials create a direct secret-exposure risk and must be removed immediately.",
            risk_flags=["Hardcoded credentials", "Secret exposure", "Immediate rotation required"],
        )
    ]

    drift = ArchitecturalDrift(
        violates_patterns=True,
        explanation="This change introduces hardcoded cloud credentials in source control, which is a critical security violation.",
    )

    return AnalyzeDiffResponse(summary=summary, review_roadmap=review_roadmap, architectural_drift=drift)


async def _call_gemini_with_retries(diff_text: str, max_retries: int = 2) -> AnalyzeDiffResponse | None:
    if not httpx or not settings.gemini_api_key:
        return None

    prompt = (
        _LLM_PROMPT
        + "\nUse the following git diff as the source of truth and respond with valid JSON only.\n\n"
        + diff_text
    )

    attempt = 0
    last_raw = None
    async with httpx.AsyncClient(timeout=60.0) as client:
        while attempt <= max_retries:
            attempt += 1
            try:
                for model_name in [settings.gemini_model, "gemini-2.0-flash-lite", "gemini-1.5-flash"]:
                    if not model_name:
                        continue

                    url = (
                        f"https://generativelanguage.googleapis.com/v1beta/models/"
                        f"{model_name}:generateContent?key={settings.gemini_api_key}"
                    )

                    payload = {
                        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
                        "generationConfig": {
                            "temperature": 0,
                            "maxOutputTokens": 2048,
                            "responseMimeType": "application/json",
                        },
                    }

                    response = await client.post(url, json=payload)
                    if response.status_code == 429:
                        continue
                    response.raise_for_status()
                    data = response.json()
                    candidates = data.get("candidates", [])
                    if not candidates:
                        continue

                    parts = candidates[0].get("content", {}).get("parts", [])
                    text = "".join(part.get("text", "") for part in parts if isinstance(part, dict))
                    last_raw = text
                    parsed = _extract_json_payload(text)
                    errors = _validate_json_struct(parsed)
                    if not errors:
                        return AnalyzeDiffResponse.parse_obj(parsed)

                    if attempt <= max_retries:
                        prompt = (
                            "Fix this JSON to match the schema exactly: "
                            f"{errors}. Return JSON only.\n\n{last_raw}"
                        )
                        break
            except Exception:
                pass

    return None


async def _call_ollama_with_retries(diff_text: str, max_retries: int = 2) -> AnalyzeDiffResponse | None:
    if not httpx:
        return None

    messages = [
        {"role": "system", "content": _LLM_PROMPT},
        {
            "role": "user",
            "content": (
                "Use the following git diff as the source of truth and respond with valid JSON only.\n\n"
                + diff_text
            ),
        },
    ]

    attempt = 0
    last_text = None
    while attempt <= max_retries:
        attempt += 1
        try:
            text = await ollama_chat(
                base_url=settings.ollama_base_url,
                model=settings.ollama_model,
                messages=messages,
                temperature=0.0,
                timeout=120.0,
                response_format="json",
            )
            if not text:
                return None

            last_text = text
            parsed = _extract_json_payload(text)
            errors = _validate_json_struct(parsed)
            if not errors:
                return AnalyzeDiffResponse.parse_obj(parsed)

            if attempt <= max_retries:
                messages = [
                    {"role": "system", "content": _LLM_PROMPT},
                    {
                        "role": "user",
                        "content": (
                            "Fix this JSON to match the schema exactly. Return JSON only.\n\n"
                            f"Validation errors: {errors}\n\n{last_text}"
                        ),
                    },
                ]
        except Exception:
            pass

    return None


async def _call_llm_with_retries(diff_text: str, max_retries: int = 2) -> AnalyzeDiffResponse | None:
    # If a local mock was requested at runtime, prefer it (helpful for tests that set the flag after import)
    global openai
    if settings.use_local_llm_mock:
        try:
            from . import llm_mock as _mock

            openai = _mock  # type: ignore
        except Exception:
            pass

    if not openai or (not settings.openai_api_key and not settings.use_local_llm_mock):
        return None

    # if real OpenAI, set the API key
    try:
        openai.api_key = settings.openai_api_key
    except Exception:
        pass

    attempt = 0
    last_raw = None
    while attempt <= max_retries:
        attempt += 1
        try:
            # If structured output is requested and the client supports it, try function-calling/schema route
            if settings.use_structured_output:
                try:
                    resp = openai.ChatCompletion.create(
                        model="gpt-3.5-turbo",
                        messages=[
                            {"role": "system", "content": _LLM_PROMPT},
                            {"role": "user", "content": diff_text},
                        ],
                        functions=[{"name": "structured_output", "parameters": JSON_SCHEMA}],
                        function_call={"name": "structured_output"},
                        max_tokens=1000,
                        temperature=0.0,
                    )
                except Exception:
                    # fall back to standard call if function-calling not supported
                    resp = openai.ChatCompletion.create(
                        model="gpt-3.5-turbo",
                        messages=[
                            {"role": "system", "content": _LLM_PROMPT},
                            {"role": "user", "content": diff_text},
                        ],
                        max_tokens=1000,
                        temperature=0.0,
                    )
            else:
                resp = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": _LLM_PROMPT},
                        {"role": "user", "content": diff_text},
                    ],
                    max_tokens=1000,
                    temperature=0.0,
                )
            # Prefer function_call.arguments if present (structured output)
            choice_msg = resp.choices[0].message
            # support both attribute-style and dict-style responses
            function_call = None
            try:
                function_call = getattr(choice_msg, 'function_call', None)
            except Exception:
                try:
                    function_call = choice_msg.get('function_call')
                except Exception:
                    function_call = None

            if function_call and isinstance(function_call, dict) and 'arguments' in function_call:
                text = function_call['arguments']
            else:
                try:
                    text = getattr(choice_msg, 'content')
                except Exception:
                    try:
                        text = choice_msg.get('content')
                    except Exception:
                        text = None

            last_raw = text
            # try to extract JSON
            if not text:
                parsed = {}
            else:
                start = text.find('{')
                if start != -1:
                    try:
                        parsed = json.loads(text[start:])
                    except Exception:
                        parsed = json.loads(text)
                else:
                    parsed = json.loads(text)

            # validate schema
            errors = _validate_json_struct(parsed)
            if not errors:
                return AnalyzeDiffResponse.parse_obj(parsed)

            # If validation errors, ask the model to correct only the JSON
            if attempt <= max_retries:
                repair_prompt = (
                    "The JSON you returned did not match the required schema. "
                    f"Validation errors: {errors}.\nPlease provide only corrected JSON that matches the schema exactly, and nothing else."
                )
                # ask for correction
                try:
                    resp2 = openai.ChatCompletion.create(
                        model="gpt-3.5-turbo",
                        messages=[
                            {"role": "system", "content": _LLM_PROMPT},
                            {"role": "user", "content": repair_prompt},
                            {"role": "assistant", "content": last_raw},
                        ],
                        max_tokens=1000,
                        temperature=0.0,
                    )
                    text2 = resp2.choices[0].message.content
                    last_raw = text2
                    start2 = text2.find('{')
                    if start2 != -1:
                        text2 = text2[start2:]
                    parsed2 = json.loads(text2)
                    errors2 = _validate_json_struct(parsed2)
                    if not errors2:
                        return AnalyzeDiffResponse.parse_obj(parsed2)
                    # loop to retry
                except Exception:
                    # fallthrough to retry loop
                    pass
        except Exception:
            # Try again until attempts exhausted
            pass

    return None


async def analyze_diff(diff_text: str, repo: str | None = None, tenant: str | None = None) -> AnalyzeDiffResponse:
    secret_result = _build_secret_exposure_response(diff_text)
    if secret_result:
        return secret_result

    # Try free local Ollama first.
    if settings.use_llm and settings.llm_provider in ("ollama", "auto"):
        ollama_result = await _call_ollama_with_retries(diff_text, max_retries=2)
        if ollama_result:
            return ollama_result

    # Try Gemini if explicitly selected.
    if settings.use_llm and settings.llm_provider == "gemini" and settings.gemini_api_key:
        gemini_result = await _call_gemini_with_retries(diff_text, max_retries=2)
        if gemini_result:
            return gemini_result

    # Try OpenAI/local mock if explicitly selected.
    if settings.use_llm and (settings.llm_provider == "openai" or settings.use_local_llm_mock) and settings.openai_api_key:
        llm_result = await _call_llm_with_retries(diff_text, max_retries=2)
        if llm_result:
            return llm_result

    # Fallback heuristic analysis
    files = parse_diff(diff_text)
    total = len(files)
    total_changes = sum(f.get("added_lines", 0) + f.get("removed_lines", 0) for f in files)

    if total_changes < 10:
        load = "Low"
    elif total_changes < 100:
        load = "Medium"
    else:
        load = "High"

    summary = Summary(
        intent=("Analyze git diff for review roadmap"),
        cognitive_load_score=load,
        total_impacted_modules=total,
    )

    review_roadmap: List[RoadmapItem] = []
    priority = 1
    for f in files:
        review_roadmap.append(
            RoadmapItem(
                file_path=f["file_path"],
                review_priority=priority,
                change_type=f.get("change_type", "Modified"),
                architectural_impact=None,
                risk_flags=[],
            )
        )
        priority += 1

    drift = ArchitecturalDrift(violates_patterns=False, explanation=None)

    await asyncio.sleep(0)
    return AnalyzeDiffResponse(summary=summary, review_roadmap=review_roadmap, architectural_drift=drift)
