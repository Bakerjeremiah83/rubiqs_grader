# app/utils/auth_decorators.py
from __future__ import annotations

from functools import wraps

from flask import redirect, session, url_for

__all__ = ["login_required", "has_tool", "require_tool", "require_superuser"]


def _is_logged_in() -> bool:
    return bool(
        session.get("logged_in")
        or session.get("launch_data")
        or session.get("user_id")
        or session.get("student_id")
        or session.get("instructor_id")
        or session.get("is_superuser")
    )


def _safe_redirect():
    # Try known endpoints; fall back to "/"
    for ep in ("lti.unauthorized", "manual_login", "index"):
        try:
            return redirect(url_for(ep))
        except Exception:
            continue
    return redirect("/")


# ---- Back-compat shim (used by app.routes.auth on Render) ----
def login_required(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        if _is_logged_in():
            return view(*args, **kwargs)
        return _safe_redirect()

    return wrapper


# ---- Capability checks exposed to templates (main.py registers this) ----
def has_tool(tool: str | None) -> bool:
    if session.get("is_superuser"):
        return True
    if not tool:
        return _is_logged_in()

    # Common shapes:
    # 1) session["tool_access"] = {"grader": True, "notes": True, "speak": True}
    access = session.get("tool_access") or session.get("tools") or {}
    if isinstance(access, dict) and access.get(tool):
        return True

    # 2) Flat flags like access_grader / access_notes / access_speak
    if session.get(f"access_{tool}") or session.get(f"{tool}_access"):
        return True

    return False


def require_tool(tool: str | None):
    def decorator(view):
        @wraps(view)
        def wrapper(*args, **kwargs):
            if not _is_logged_in():
                return _safe_redirect()
            if tool and not has_tool(tool):
                # Prefer a friendly unauthorized page if you have one
                try:
                    return redirect(url_for("lti.unauthorized"))
                except Exception:
                    return ("Forbidden", 403)
            return view(*args, **kwargs)

        return wrapper

    return decorator


def require_superuser(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        if session.get("is_superuser"):
            return view(*args, **kwargs)
        try:
            return redirect(url_for("lti.unauthorized"))
        except Exception:
            return ("Forbidden", 403)

    return wrapper
