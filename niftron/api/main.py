# niftron/api/main.py

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
import datetime
from typing import List, Dict, Any
from cachetools import cached, TTLCache
from fastapi.middleware.cors import CORSMiddleware
from niftron.analysis.backtest import get_backtest_results
from niftron.core.db import get_db_connection
from niftron.analysis.main import run_analysis_and_rank
from niftron.analysis import backtest
import pandas as pd
from niftron.chatbot import generate_ai_response
from pydantic import BaseModel
from niftron.data_access.recommendations import get_latest_recommendations_from_db

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    reply: str

class Recommendation(BaseModel):
    """Defines the structure for a single stock recommendation."""
    rank: int
    symbol: str
    company_name: str
    score: float = Field(..., description="The final ensembled score.")
    algorithm_scores: Dict[str, Any] = Field(..., description="Scores from individual algorithms.")

class RecommendationResponse(BaseModel):
    """Defines the structure for the final API response with both model results."""
    date: datetime.date
    she_recommendations: List[Recommendation]
    lem_recommendations: List[Recommendation]
    
# --- FastAPI Application ---

app = FastAPI(title="Niftron API", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])


# --- ADD THIS ENTIRE BLOCK ---
# This enables Cross-Origin Resource Sharing (CORS)
# It allows your frontend (running on localhost:3000) to make requests to this backend.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins for development
    allow_credentials=True,
    allow_methods=["*"],  # Allows all HTTP methods
    allow_headers=["*"],  # Allows all headers
)
# --- END OF BLOCK TO ADD ---


# --- Your existing endpoints ---
# No changes needed to the functions below this line.
@app.get("/api/v1/recommendations", response_model=RecommendationResponse)
def get_latest_recommendations():
    try:
        date, lem_recs, she_recs = get_latest_recommendations_from_db()
        if not date: raise HTTPException(status_code=404, detail="No recommendations found.")
        return RecommendationResponse(date=date, lem_recommendations=lem_recs, she_recommendations=she_recs)
    except Exception as e: raise HTTPException(status_code=500, detail=f"Internal server error: {e}")

@app.post("/api/v1/chat", response_model=ChatResponse)
def handle_chat_message(request: ChatRequest):
    ai_reply = generate_ai_response(request.message)
    return ChatResponse(reply=ai_reply)

@app.get("/api/v1/performance", response_model=Dict[str, Any])
def get_performance_metrics():
    """
    Runs the full backtest simulation and returns key performance metrics
    for the LEM, SHE, and Benchmark strategies.
    """
    print("API endpoint /api/v1/performance hit. Running backtest...")
    results = get_backtest_results()
    print("Backtest complete. Returning results.")
    return results

# in niftron/api/main.py

# Create a new cache specifically for chart data
chart_cache = TTLCache(maxsize=10, ttl=43200) # 12-hour TTL


@app.get("/api/v1/charts/equity-curve")
def get_equity_curve_data():
    """
    Calculates and returns data for the equity curve chart, formatted for Chart.js.
    """
    # 1. Get the cached daily returns
    lem_daily_returns, she_daily_returns, benchmark_daily_returns = backtest.run_all_simulations()

    # 2. Calculate cumulative returns
    returns_df = pd.DataFrame({
        'LEM': lem_daily_returns,
        'SHE': she_daily_returns,
        'Benchmark': benchmark_daily_returns
    })
    cumulative_df = (1 + returns_df).cumprod()

    # 3. Format for Chart.js
    chart_data = {
        "labels": cumulative_df.index.strftime('%Y-%m-%d').tolist(),
        "datasets": [
            { "label": "Learned Ensemble (LEM)", "data": cumulative_df['LEM'].tolist(), "borderColor": "#3b82f6", "tension": 0.1, "pointRadius": 0, "borderWidth": 2 },
            { "label": "Simple Heuristic (SHE)", "data": cumulative_df['SHE'].tolist(), "borderColor": "#10b981", "tension": 0.1, "pointRadius": 0, "borderWidth": 2 },
            { "label": "NIFTY 50 Benchmark", "data": cumulative_df['Benchmark'].tolist(), "borderColor": "#6b7280", "tension": 0.1, "pointRadius": 0, "borderWidth": 2 },
        ]
    }
    return chart_data

@app.post("/api/v1/run-analysis", status_code=200)
def trigger_run_analysis():
    """
    Triggers the daily analysis pipeline to re-calculate and store the latest recommendations.
    This is an asynchronous task on the server. The endpoint will return immediately.
    """
    try:
        print("API endpoint /api/v1/run-analysis hit. Triggering analysis.")
        # In a production system, you would run this as a background task.
        # For our case, running it directly is fine.
        run_analysis_and_rank()
        return {"message": "Analysis pipeline triggered successfully. New recommendations are being generated."}
    except Exception as e:
        print(f"Error during analysis run: {e}")
        raise HTTPException(status_code=500, detail="An error occurred while running the analysis.")


@app.post("/api/v1/chat", response_model=ChatResponse)
def handle_chat_message(request: ChatRequest):
    """Receives a user message and returns a response from the AI chatbot."""
    print(f"Chat endpoint hit with message: '{request.message}'")
    ai_reply = generate_ai_response(request.message)
    return ChatResponse(reply=ai_reply)

@app.get("/")
def read_root():
    return {"message": "Welcome to the Niftron API. Visit /docs for documentation."}