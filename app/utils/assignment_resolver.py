# app/utils/assignment_resolver.py
from typing import Dict, Optional, Tuple
from flask import request
from app.supabase_client import supabase

def _get_custom_param(launch_data: dict, key: str) -> Optional[str]:
    # LTI 1.3 custom params usually appear under this claim
    custom = launch_data.get("https://purl.imsglobal.org/spec/lti/claim/custom") or {}
    val = custom.get(key)
    if isinstance(val, str) and val.strip():
        return val.strip()
    return None

def resolve_assignment_from_launch(launch_data: dict, req) -> Tuple[Optional[Dict], Optional[str], Optional[str]]:
    """
    Returns: (assignment_row_or_None, resolved_display_title, resolved_slug)
    Resolution priority:
      1) URL query ?slug=... (handy for testing)
      2) LTI custom param assignment_slug
      3) LTI resource_link.title (normalize as plain string match on display/title)
    """
    # 1) URL override for dev/test
    slug = (req.args.get("slug") or "").strip().lower()
    if slug:
        row = (
            supabase.table("assignments")
            .select("*")
            .eq("tool", "grader")
            .eq("slug", slug)
            .limit(1)
            .execute()
        ).data
        if row:
            a = row[0]
            return a, (a.get("display_title") or a.get("assignment_title")), a.get("slug")

    # 2) LTI custom param
    if launch_data:
        slug = (_get_custom_param(launch_data, "assignment_slug") or "").lower()
        if slug:
            row = (
                supabase.table("assignments")
                .select("*")
                .eq("tool", "grader")
                .eq("slug", slug)
                .limit(1)
                .execute()
            ).data
            if row:
                a = row[0]
                return a, (a.get("display_title") or a.get("assignment_title")), a.get("slug")

    # 3) Fallback to resource_link.title string match
    title = ""
    if launch_data:
        rl = launch_data.get("https://purl.imsglobal.org/spec/lti/claim/resource_link") or {}
        title = (rl.get("title") or "").strip()

    if title:
        # Prefer display_title match, fallback to assignment_title
        row = (
            supabase.table("assignments")
            .select("*")
            .eq("tool", "grader")
            .or_(f"display_title.eq.{title},assignment_title.eq.{title}")
            .limit(1)
            .execute()
        ).data
        if row:
            a = row[0]
            return a, (a.get("display_title") or a.get("assignment_title")), a.get("slug")

    return None, None, None
