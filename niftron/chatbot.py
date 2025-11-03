# niftron/chatbot.py
import os
import re
import json
import google.generativeai as genai
from niftron.data_access.recommendations import get_latest_recommendations_from_db
from niftron.core.db import get_db_connection

# --- (Gemini configuration is the same) ---
try:
    genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
    model = genai.GenerativeModel('gemini-2.5-flash')
except Exception as e:
    print(f"ERROR: Could not configure Gemini API. Check GEMINI_API_KEY. Error: {e}")
    model = None

def get_detailed_scores_for_symbol(symbol: str, date):
    """Fetches the specific algorithm scores for a given stock symbol on a given date."""
    query = """
        SELECT algorithm_scores FROM recommendations
        WHERE symbol = %s AND date = %s
        LIMIT 1;
    """
    # A bit inefficient to query again, but good for modularity.
    # We need to get the symbol's stock_id first.
    query_scores = """
        SELECT r.algorithm_scores
        FROM recommendations r
        JOIN stocks s ON r.stock_id = s.stock_id
        WHERE s.symbol = %s AND r.date = %s;
    """
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query_scores, (symbol.upper(), date))
            result = cur.fetchone()
            if result and result[0]:
                # The result is a dict/json, return it
                return result[0]
    return None

def get_context_for_prompt(user_query: str):
    """
    Gathers general context, and if a stock symbol is mentioned,
    fetches detailed context for that specific stock.
    """
    try:
        date, lem_recs, she_recs = get_latest_recommendations_from_db()
        if not date: return "No recommendation data available."

        # --- General Context ---
        context = f"Today's Date: {date.strftime('%Y-%m-%d')}\n"
        context += "--- Top 5 ML Model (LEM) Recommendations ---\n"
        for rec in lem_recs:
            context += f"- Rank {rec['rank']}: {rec['symbol']}, Score: {rec['score']:.2f}\n"
        
        # --- NEW: Dynamic Context Injection ---
        # Find any stock symbols mentioned in the user's query
        mentioned_symbols = re.findall(r'\b([A-Z&]+)\b', user_query.upper())
        if mentioned_symbols:
            symbol = mentioned_symbols[0] # Focus on the first symbol found
            
            # Check if this symbol is in our recommendations
            all_recs = {rec['symbol']: rec for rec in lem_recs + she_recs}
            if symbol in all_recs:
                detailed_scores = all_recs[symbol].get('algorithm_scores')
                if detailed_scores:
                    context += f"\n--- Detailed Scores for {symbol} ---\n"
                    context += f"- Trend Signal: {detailed_scores.get('trend_signal', 'N/A')}\n"
                    context += f"- Momentum Score: {detailed_scores.get('momentum_score', 'N/A')}\n"
                    context += f"- MACD Score: {detailed_scores.get('macd_score', 'N/A')}\n"
                    context += "(Note: Trend is -1, 0, or 1. Momentum and MACD are 0-100)."
        
        return context
    except Exception:
        return "Could not fetch recommendation data."

def generate_ai_response(user_query: str):
    if not model:
        return "Error: The AI model is not configured correctly on the server."
    
    # The context is now generated based on the user's query
    context = get_context_for_prompt(user_query)
    
    system_prompt = f"""
    You are NIFTRON, a helpful and concise AI financial analyst for an Indian stock market app.
    Your main goal is to answer user questions based *only* on the context provided below.
    - When asked about a specific stock, use the "Detailed Scores" to explain WHY it was recommended (e.g., "It has a strong momentum score").
    - Do not give any financial advice, price predictions, or information not present in the context.
    - Keep your answers short and to the point.

    CONTEXT:
    {context}
    """
    try:
        response = model.generate_content(system_prompt + "\n\nUser Question: " + user_query)
        return response.text
    except Exception as e:
        return f"An error occurred while communicating with the AI model: {e}"