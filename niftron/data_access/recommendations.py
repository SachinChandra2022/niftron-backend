import datetime
from typing import List, Dict, Any, Tuple
from niftron.core.db import get_db_connection

def get_latest_recommendations_from_db() -> Tuple[datetime.date, List[Dict[str, Any]], List[Dict[str, Any]]]:
    query = """
        SELECT r.date, r.rank, s.symbol, s.company_name, 
               r.score, r.algorithm_scores, r.model_type
        FROM recommendations r
        JOIN stocks s ON r.stock_id = s.stock_id
        WHERE r.date = (SELECT MAX(date) FROM recommendations)
        ORDER BY r.model_type, r.rank ASC;
    """
    she_recs, lem_recs, recommendation_date = [], [], None
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query)
            results = cur.fetchall()
            if not results:
                return None, [], []
            recommendation_date = results[0][0]
            for row in results:
                rec = {"rank": row[1], "symbol": row[2], "company_name": row[3], "score": row[4], "algorithm_scores": row[5]}
                if row[6] == 'SHE': she_recs.append(rec)
                elif row[6] == 'LEM': lem_recs.append(rec)
    return recommendation_date, lem_recs, she_recs

