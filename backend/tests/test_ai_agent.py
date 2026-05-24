import asyncio
from ..app.services import llm_mock
from ..app.services import ai_agent
from ..app.config import settings


SAMPLE_DIFF = """diff --git a/README.md b/README.md
index 83db48f..bf3f4e2 100644
--- a/README.md
+++ b/README.md
@@ -1,3 +1,6 @@
+Added a new line
"""


def test_llm_valid_response(monkeypatch):
    # Use local mock
    settings.use_local_llm_mock = True
    settings.use_llm = True
    settings.openai_api_key = 'sk-test'
    # use real validation
    llm_mock.queue_response('{"summary": {"intent":"Test","cognitive_load_score":"Low","total_impacted_modules":1}, "review_roadmap": [{"file_path":"README.md","review_priority":1,"change_type":"Modified","architectural_impact":null,"risk_flags":[]}], "architectural_drift": {"violates_patterns": false}}')

    res = asyncio.get_event_loop().run_until_complete(ai_agent.analyze_diff(SAMPLE_DIFF))
    assert res.summary.intent == "Test"
    assert res.summary.cognitive_load_score == "Low"


def test_llm_invalid_then_repair(monkeypatch):
    settings.use_local_llm_mock = True
    settings.use_llm = True
    settings.openai_api_key = 'sk-test'
    # First response missing summary
    llm_mock.queue_response('{"review_roadmap": [], "architectural_drift": {"violates_patterns": false}}')
    # Second (repair) response valid
    llm_mock.queue_response('{"summary": {"intent":"Repaired","cognitive_load_score":"Medium","total_impacted_modules":2}, "review_roadmap": [], "architectural_drift": {"violates_patterns": false}}')

    # use real validation (first queued response invalid, second valid)

    res = asyncio.get_event_loop().run_until_complete(ai_agent.analyze_diff(SAMPLE_DIFF))
    assert res.summary.intent == "Repaired"
    assert res.summary.cognitive_load_score == "Medium"


def test_structured_output_call(monkeypatch):
    settings.use_local_llm_mock = True
    settings.use_llm = True
    settings.openai_api_key = 'sk-test'
    settings.use_structured_output = True
    # use real validation
    # Queue a valid response
    llm_mock.queue_response('{"summary": {"intent":"Struct","cognitive_load_score":"Low","total_impacted_modules":0}, "review_roadmap": [], "architectural_drift": {"violates_patterns": false}}')

    res = asyncio.get_event_loop().run_until_complete(ai_agent.analyze_diff(SAMPLE_DIFF))
    # confirm we got the expected intent
    assert res.summary.intent == "Struct"
    # ensure the mock captured a functions kwarg when structured output requested
    assert llm_mock.last_call_kwargs is not None
    # the mock will record kwargs including 'functions' when used
    assert 'functions' in llm_mock.last_call_kwargs
