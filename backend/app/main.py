from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .models.schemas import AnalyzeDiffRequest, AnalyzeDiffResponse, CoachRequest, CoachResponse
from .services.ai_agent import analyze_diff
from .services.coach_service import get_coach_response

app = FastAPI(title="SynapsePR Backend")

app.add_middleware(
	CORSMiddleware,
	allow_origins=["*"],
	allow_credentials=True,
	allow_methods=["*"],
	allow_headers=["*"],
)


@app.get("/health")
def health():
	return {"status": "ok"}


@app.post("/api/analyze-diff", response_model=AnalyzeDiffResponse)
async def analyze(payload: AnalyzeDiffRequest):
	if not payload.diff_text or not payload.diff_text.strip():
		raise HTTPException(status_code=400, detail="Empty diff_text")

	result = await analyze_diff(payload.diff_text, repo=payload.repo, tenant=payload.tenant)
	return result


@app.post("/api/coach", response_model=CoachResponse)
async def coach(payload: CoachRequest):
	if not payload.message or not payload.message.strip():
		raise HTTPException(status_code=400, detail="Empty message")

	response = await get_coach_response(
		message=payload.message,
		intent=payload.intent,
		repo=payload.repo,
		conversation_history=payload.conversation_history,
	)
	
	if not response:
		raise HTTPException(status_code=500, detail="Failed to get coach response")
	
	return CoachResponse(response=response)
