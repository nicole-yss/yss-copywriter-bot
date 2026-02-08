"""Report generation and retrieval endpoints."""

from fastapi import APIRouter, BackgroundTasks, Request
from tools.utils.supabase_client import get_supabase_client

router = APIRouter()


@router.post("/generate")
async def generate_report(request: Request, background_tasks: BackgroundTasks):
    """
    Generate a new analytics report.

    Body:
        report_type: "content_audit" | "competitor_analysis" | "strategy"
    """
    body = await request.json()
    report_type = body.get("report_type", "content_audit")

    from tools.generate_report import generate_report as run_report
    background_tasks.add_task(run_report, report_type)

    return {"status": "started", "report_type": report_type}


@router.get("/")
async def list_reports(limit: int = 20):
    """List all generated reports."""
    supabase = get_supabase_client()
    response = (
        supabase.table("reports")
        .select("id, report_type, title, summary, created_at")
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
    )
    return response.data


@router.get("/{report_id}")
async def get_report(report_id: str):
    """Get a specific report with full content."""
    supabase = get_supabase_client()
    response = (
        supabase.table("reports")
        .select("*")
        .eq("id", report_id)
        .execute()
    )
    if response.data:
        return response.data[0]
    return {"error": "Report not found"}
