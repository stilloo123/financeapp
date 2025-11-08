"""API endpoints for PayOffOrInvest."""

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
import uuid
import json
import asyncio

from backend.agents.orchestrator import AnalysisOrchestrator

app = FastAPI(title="PayOffOrInvest API", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Update this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage for Phase 1 (use Redis in production)
analyses: Dict[str, Dict[str, Any]] = {}


class MortgageInput(BaseModel):
    balance: float = Field(..., gt=0, description="Mortgage balance remaining")
    rate: float = Field(..., gt=0, le=20, description="Interest rate percentage")
    years: int = Field(..., gt=0, le=30, description="Years remaining")


class FinancialInput(BaseModel):
    portfolio: float = Field(..., gt=0, description="Total investment portfolio")
    stock_allocation_pct: float = Field(..., ge=0, le=100, description="Percentage of portfolio in stocks (rest in bonds)")
    income: Optional[float] = Field(None, gt=0, description="Annual additional income (if any)")
    income_years: Optional[int] = Field(None, gt=0, description="Number of years income will continue")
    spending: float = Field(..., gt=0, description="Annual spending")
    spending_includes_mortgage: bool = Field(..., description="Does spending include mortgage payment?")


class AnalysisRequest(BaseModel):
    age: int = Field(..., ge=18, le=100, description="Current age")
    employment_status: str = Field(..., pattern="^(working|retired)$", description="Employment status")
    mortgage: MortgageInput
    financial: FinancialInput

    class Config:
        schema_extra = {
            "example": {
                "age": 55,
                "employment_status": "retired",
                "mortgage": {
                    "balance": 500000,
                    "rate": 3.0,
                    "years": 25
                },
                "financial": {
                    "portfolio": 5000000,
                    "spending": 200000,
                    "spending_includes_mortgage": True
                }
            }
        }


@app.get("/")
async def root():
    """Health check endpoint."""
    return {"status": "ok", "service": "PayOffOrInvest API"}


@app.post("/api/analyze")
async def create_analysis(request: AnalysisRequest):
    """Start a new analysis."""

    # Validate inputs based on employment status
    if request.employment_status == "working" and request.financial.income is None:
        raise HTTPException(
            status_code=400,
            detail="Income is required when you have additional income"
        )

    analysis_id = str(uuid.uuid4())

    # Store input
    analyses[analysis_id] = {
        "status": "processing",
        "input": request.dict(),
        "result": None
    }

    print(f"Created analysis {analysis_id}")

    return {
        "analysis_id": analysis_id,
        "status": "processing"
    }


@app.get("/api/analysis/{analysis_id}/progress")
async def get_analysis_progress(analysis_id: str):
    """Stream analysis progress via SSE."""
    if analysis_id not in analyses:
        raise HTTPException(status_code=404, detail="Analysis not found")

    async def event_generator():
        try:
            orchestrator = AnalysisOrchestrator()
            user_input = analyses[analysis_id]["input"]

            print(f"Starting analysis for {analysis_id}")

            async for update in orchestrator.analyze(user_input):
                # Format as SSE
                data = json.dumps(update)
                yield f"data: {data}\n\n"

                print(f"Progress update: {update.get('agent')} - {update.get('status')}")

                if update.get("agent") == "complete":
                    # Store result
                    analyses[analysis_id]["status"] = "complete"
                    analyses[analysis_id]["result"] = update["result"]
                    print(f"Analysis {analysis_id} complete")
                    break

        except Exception as e:
            print(f"Error in analysis {analysis_id}: {str(e)}")
            error_data = json.dumps({
                "agent": "error",
                "status": "error",
                "message": f"Error: {str(e)}"
            })
            yield f"data: {error_data}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )


@app.get("/api/analysis/{analysis_id}/results")
async def get_analysis_results(analysis_id: str):
    """Get completed analysis results."""
    if analysis_id not in analyses:
        raise HTTPException(status_code=404, detail="Analysis not found")

    analysis = analyses[analysis_id]

    if analysis["status"] != "complete":
        return {
            "status": "processing",
            "result": None
        }

    return {
        "status": "complete",
        "result": analysis["result"]
    }


@app.delete("/api/analysis/{analysis_id}")
async def delete_analysis(analysis_id: str):
    """Delete an analysis from storage."""
    if analysis_id not in analyses:
        raise HTTPException(status_code=404, detail="Analysis not found")

    del analyses[analysis_id]
    return {"message": "Analysis deleted"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
