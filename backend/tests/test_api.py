import httpx
import pytest
from httpx import AsyncClient

from backend.app.main import app


@pytest.mark.asyncio
async def test_health():
    async with AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as ac:
        r = await ac.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_analyze_empty():
    async with AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as ac:
        r = await ac.post("/api/analyze-diff", json={"diff_text": ""})
    assert r.status_code == 400


@pytest.mark.asyncio
async def test_analyze_minimal():
    diff = """
diff --git a/README.md b/README.md
index 000..111
--- a/README.md
+++ b/README.md
@@
++ Added line
"""

    async with AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as ac:
        r = await ac.post("/api/analyze-diff", json={"diff_text": diff})

    assert r.status_code == 200
    data = r.json()
    assert "summary" in data
    assert "review_roadmap" in data


@pytest.mark.asyncio
async def test_coach_empty_message():
    async with AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as ac:
        r = await ac.post("/api/coach", json={"message": ""})
    assert r.status_code == 400


@pytest.mark.asyncio
async def test_coach_returns_local_response_without_key():
    payload = {
        "message": "What should I review first?",
        "repo": "notes-api",
        "intent": "Analyze git diff for review roadmap",
        "conversation_history": [],
    }
    async with AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as ac:
        r = await ac.post("/api/coach", json=payload)

    assert r.status_code == 200
    data = r.json()
    assert "response" in data
    assert isinstance(data["response"], str)
    assert data["response"].strip()
    assert "offline" not in data["response"].lower()

