from fastapi import APIRouter
from sqlalchemy import text
from datetime import datetime, timedelta
from app.database import engine_tools

router = APIRouter()

@router.get("/analytics/dashboard")
async def get_dashboard_analytics(period: str = "1_month"):
    with engine_tools.connect() as conn:
        now = datetime.now()
        start_date = None
        end_date = now 
        
        if period == "1_month":
            start_date = now - timedelta(days=30)
        elif period == "winter_2026":
            start_date = datetime(2026, 1, 1)
            end_date = datetime(2026, 4, 30, 23, 59, 59)
        elif period == "fall_2025":
            start_date = datetime(2025, 9, 1)
            end_date = datetime(2025, 12, 31, 23, 59, 59)
        elif period == "summer_2025":
            start_date = datetime(2025, 5, 1)
            end_date = datetime(2025, 8, 31, 23, 59, 59)
        elif period == "winter_2025":
            start_date = datetime(2025, 1, 1)
            end_date = datetime(2025, 4, 30, 23, 59, 59)
        else:
            start_date = now - timedelta(days=30)

        params = {"start_date": start_date, "end_date": end_date}
        
        total_tools = conn.execute(text("SELECT COUNT(*) FROM tools")).scalar()
        current_borrowed = conn.execute(
            text("SELECT COUNT(*) FROM transactions WHERE return_timestamp IS NULL")
        ).scalar()
        current_overdue = conn.execute(
            text("SELECT COUNT(*) FROM transactions WHERE return_timestamp IS NULL AND desired_return_date < NOW()")
        ).scalar()

        period_checkouts = conn.execute(
            text("SELECT COUNT(*) FROM transactions WHERE checkout_timestamp >= :start_date AND checkout_timestamp <= :end_date"),
            params
        ).scalar()

        top_tools_result = conn.execute(
            text("""
                SELECT t.tool_name, COUNT(tr.tool_id) as usage_count
                FROM transactions tr
                JOIN tools t ON tr.tool_id = t.tool_id
                WHERE tr.checkout_timestamp >= :start_date AND tr.checkout_timestamp <= :end_date
                GROUP BY tr.tool_id, t.tool_name
                ORDER BY usage_count DESC
                LIMIT 10
            """),
            params
        ).fetchall()
        
        top_tools = [{"name": row.tool_name, "uses": row.usage_count} for row in top_tools_result]

        return {
            "live_stats": {
                "total_tools": total_tools,
                "current_borrowed": current_borrowed,
                "current_overdue": current_overdue,
            },
            "period_stats": {
                "checkouts": period_checkouts,
                "top_tools": top_tools,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            }
        }
