# app/routes/auth.py — grader-only friendly auth

import os
import uuid
from datetime import datetime, timedelta
from urllib.parse import urlencode

from flask import (
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from werkzeug.security import check_password_hash, generate_password_hash

from app.routes import lti
from app.supabase_client import supabase
from app.utils.auth_decorators import login_required, require_tool

# -------------------------
# LTI OIDC entry (unchanged)
# -------------------------
@lti.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return redirect(url_for("lti.rubiqs_suite_login"))

    print("🔐 /login route hit")

    env_client_id = (os.getenv("CLIENT_ID") or "").strip()
    env_client_ids_raw = os.getenv("CLIENT_IDS") or ""
    env_client_ids = {c.strip() for c in env_client_ids_raw.split(",") if c.strip()}
    if env_client_id:
        env_client_ids.add(env_client_id)

    form = request.form
    issuer = (form.get("iss") or "").strip()
    login_hint = form.get("login_hint") or ""
    target_link_uri = form.get("target_link_uri") or url_for("lti.launch", _external=True)
    client_id = (form.get("client_id") or "").strip()
    lti_message_hint = form.get("lti_message_hint") or ""

    if not all([issuer, login_hint, target_link_uri, client_id]):
        return "❌ Missing required LTI launch parameters", 400
    if client_id not in env_client_ids:
        return f"❌ Invalid client ID: {client_id}", 403

    session["oidc_client_id"] = client_id
    session.permanent = True
    state = uuid.uuid4().hex
    nonce = uuid.uuid4().hex
    session["oidc_state"] = state
    session["oidc_nonce"] = nonce

    auth_url = f"{issuer.rstrip('/')}/mod/lti/auth.php"
    params = {
        "scope": "openid",
        "response_type": "id_token",
        "response_mode": "form_post",
        "client_id": client_id,
        "redirect_uri": target_link_uri,
        "login_hint": login_hint,
        "state": state,
        "nonce": nonce,
        "prompt": "none",
        "lti_message_hint": lti_message_hint,
        "target_link_uri": target_link_uri,
    }
    return redirect(f"{auth_url}?{urlencode(params)}")


# --------------------------------------
# Password form (DB first, then env fallback)
# --------------------------------------
@lti.route("/rubiqs-suite-login", methods=["GET", "POST"])
def rubiqs_suite_login():
    """
    POST behavior:
    1) Try Supabase users table (email + password hash).
    2) If not found or disabled locally, allow a shared password via GRADER_PASSWORD
       (username can be anything; this is just for local/dev).
    On success: set session keys expected by @require_tool('grader') and redirect to /grader.
    """
    error = None
    if request.method == "GET":
        return render_template("login.html", error=None)

    email = (request.form.get("username") or "").strip().lower()
    password = request.form.get("password") or ""
    if not password:
        return render_template("login.html", error="Invalid username or password")

    # --- 1) DB-backed login (if users table is set up)
    user = None
    try:
        res = supabase.table("users").select("*").eq("email", email).limit(1).execute()
        user = res.data[0] if res.data else None
    except Exception as e:
        print("ℹ️ Supabase lookup skipped/failed:", e)

    if user:
        stored_hash = user.get("password_hash") or ""
        if stored_hash and check_password_hash(stored_hash, password):
            # success
            _seed_session_from_user(user)
            return redirect(url_for("lti.grader_base"))
        else:
            # fall through to env password check below
            pass

    # --- 2) Shared password fallback for dev/local
    shared_pw = os.getenv("GRADER_PASSWORD") or os.getenv("ADMIN_PASSWORD") or ""
    if shared_pw and password == shared_pw:
        session.clear()
        session["logged_in"] = True
        session["role"] = "instructor"
        session["user_email"] = email or "instructor@local"
        session["user_id"] = os.getenv("DEV_FAKE_UID", "00000000-0000-0000-0000-000000000001")
        session["institution_id"] = None
        session["is_superuser"] = True  # convenient locally
        session["is_admin"] = True
        session["is_institution_admin"] = True

        # Crucial for @require_tool("grader")
        session["access_grader"] = True
        session.setdefault("tool_access", {})["grader"] = True

        return redirect(url_for("lti.grader_base"))

    # Fallback: invalid
    return render_template("login.html", error="Invalid username or password")


def _seed_session_from_user(user: dict):
    """Set the minimal session keys so @require_tool('grader') passes."""
    session.clear()
    role = (user.get("role") or "user").strip().lower()

    session["logged_in"] = True
    session["user_email"] = user.get("email")
    session["role"] = role
    session["user_id"] = user.get("id") or user.get("email") or "demo_user"
    session["institution_id"] = user.get("institution_id")
    session["is_superuser"] = role == "superuser"
    session["is_admin"] = role == "admin"
    session["is_institution_admin"] = role == "institution_admin"

    # Tool gates: make sure grader access is True if this user should see it
    has_grader = bool(user.get("access_grader")) or role in {"admin", "superuser", "instructor"}
    session["access_grader"] = has_grader
    # some decorators read a dict; keep both
    session["tool_access"] = {
        "grader": has_grader,
        "chat": bool(user.get("access_chat")),
        "speak": bool(user.get("access_speak")),
        "notes": bool(user.get("access_notes")),
        "math": bool(user.get("access_math")),
    }


@lti.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("lti.rubiqs_suite_login"))


@lti.route("/unauthorized")
def unauthorized():
    # If a guard denies access, send to login page
    flash("⚠ Please log in to access that page.")
    return redirect(url_for("lti.rubiqs_suite_login"))


# Optional sample protected page (kept for parity)
@lti.route("/math", methods=["GET"])
@require_tool("math")
def math_public():
    return render_template("math/math_workspace_public.html", title="Rubiqs Math")

# --- Public signup (explicit endpoint name so url_for('lti.public_signup') works) ---
@lti.route("/public-signup", methods=["GET", "POST"], endpoint="public_signup")
def public_signup():
    """
    Minimal, non-LTI public signup page.
    You can keep or expand the Supabase-backed creation logic you had before.
    This stub ensures the endpoint exists so login.html can link to it.
    """
    from flask import render_template, request, redirect, url_for, flash
    from werkzeug.security import generate_password_hash
    from app.supabase_client import supabase
    from datetime import datetime

    if request.method == "GET":
        # If you have a dedicated template, render it; otherwise reuse login with a flag.
        try:
            return render_template("auth_signup.html")
        except Exception:
            # Fallback tiny page so the endpoint never 500s if the template is missing
            return (
                "<h1>Sign up</h1>"
                "<p>Public signup page is not fully configured yet.</p>"
                "<p><a href='/rubiqs-suite-login'>Back to sign in</a></p>",
                200,
            )

    # POST: (optional) very simple account creation flow
    email = (request.form.get("email") or "").strip().lower()
    password = request.form.get("password") or ""
    if not email or not password:
        flash("Email and password are required.", "error")
        return redirect(url_for("lti.public_signup"))

    # Prevent duplicate
    existing = supabase.table("users").select("id").eq("email", email).limit(1).execute()
    if existing.data:
        flash("An account with this email already exists. Please sign in.", "error")
        return redirect(url_for("lti.rubiqs_suite_login"))

    pwd_hash = generate_password_hash(password)
    now_iso = datetime.utcnow().isoformat() + "Z"

    _ = (
        supabase.table("users")
        .insert(
            {
                "email": email,
                "password_hash": pwd_hash,
                "role": "user",
                # grant no tools by default; adjust as needed
                "access_grader": False,
                "access_chat": False,
                "access_speak": False,
                "access_notes": False,
                "access_math": False,
                "created_at": now_iso,
            }
        )
        .execute()
    )

    flash("Account created. Please sign in.", "success")
    return redirect(url_for("lti.rubiqs_suite_login"))
