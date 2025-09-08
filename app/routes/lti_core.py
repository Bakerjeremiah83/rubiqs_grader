# app/routes/lti_core.py
import json
import os
from flask import request, redirect, url_for, session
from . import lti

# --- JWKS: serve your tool's public keys (simplified placeholder) ---
# If your real JWKS is stored in env or generated from your private key,
# replace this with your working implementation.
@lti.get("/.well-known/jwks.json")
def jwks():
    # If you already have a JWKS JSON string in env, prefer that:
    jwks_env = os.getenv("TOOL_PUBLIC_JWKS")
    if jwks_env:
        return jwks_env, 200, {"Content-Type": "application/json"}
    # Otherwise serve an empty JWKS (not production-ready).
    return json.dumps({"keys": []}), 200, {"Content-Type": "application/json"}

# --- OIDC Login Initiation (optional if your flow uses it) ---
@lti.get("/oidc-login")
def oidc_login():
    # TODO: If your production flow needs OIDC initiation, paste it here.
    # For now, provide a friendly placeholder.
    return "OIDC login endpoint is configured. Paste your real initiation flow here.", 200

# --- LTI Launch (REQUIRED): LMS posts id_token here ---
@lti.post("/launch")
def launch():
    # TODO: Replace with your production id_token verification + claims parsing.
    # Minimal behavior: set a few session keys so templates/routes can work.
    session["user_id"] = session.get("user_id", "lti_user")
    session["roles"] = session.get("roles", ["Instructor"])

    # Redirect to the minimal Suite dashboard (Grader-only tile)
    return redirect(url_for("lti.suite_dashboard"))
