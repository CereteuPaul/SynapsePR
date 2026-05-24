"""Lightweight local LLM mock for testing.

Usage:
- Set `settings.use_local_llm_mock = True` in tests or env.
- Populate `queued_responses` with raw string responses (JSON or text).
"""
from types import SimpleNamespace

queued_responses = []
last_call_kwargs = None


class ChatCompletion:
    @staticmethod
    def create(*args, **kwargs):
        global last_call_kwargs
        last_call_kwargs = kwargs
        if queued_responses:
            content = queued_responses.pop(0)
        else:
            # default simple valid JSON
            content = '{"summary": {"intent":"default","cognitive_load_score":"Low","total_impacted_modules":0}, "review_roadmap": [], "architectural_drift": {"violates_patterns": false}}'

        # mimic OpenAI SDK response structure
        message = SimpleNamespace(content=content)
        choice = SimpleNamespace(message=message)
        return SimpleNamespace(choices=[choice])


def queue_response(s: str):
    queued_responses.append(s)
