# app/routes/lti_core.py
import json
import os
import time
from flask import request, redirect, url_for, session, make_response
from . import lti

# For dev-friendly id_token parsing (no signature verification).
# In production you MUST verify with the platform's JWKs.
try:
    import jwt  # PyJWT
except Exception:
    jwt = None

LTI_CLAIM_MSG_TYPE = "https://purl.imsglobal.org/spec/lti/claim/message_type"
LTI_CLAIM_VERSION  = "https://purl.imsglobal.org/spec/lti/claim/version"
LTI_CLAIM_DEPLOY   = "https://purl.imsglobal.org/spec/lti/claim/deployment_id"
LTI_CLAIM_CUSTOM   = "https://purl.imsglobal.org/spec/lti/claim/custom"
LTI_DL_SETTINGS    = "https://purl.imsglobal.org/spec/lti-dl/claim/deep_linking_settings"

def _log(s):
    print(f"[lti_core] {s}")

# ---------- JWKS (your tool's public keys) ----------
@lti.get("/.well-known/jwks.json")
def jwks():
    """
    If you sign Deep Linking Responses (you do) and you also want the LMS
    to be able to verify any tool-signed messages, expose your JWKS here.

    Set TOOL_PUBLIC_JWKS to a JSON string like: {"keys":[{...}]}
    Otherwise this returns an empty set (fine for dev).
    """
    jwks_env = os.getenv("TOOL_PUBLIC_JWKS")
    body = jwks_env if jwks_env else json.dumps({"keys": []})
    resp = make_response(body, 200)
    resp.headers["Content-Type"] = "application/json"
    return resp

# ---------- Optional OIDC initiation ----------
@lti.get("/oidc-login")
def oidc_login():
    return "OIDC login endpoint ready. (Use your existing /login route for platforms that need initiation.)", 200

# ---------- Required: LTI Launch (id_token POST) ----------
@lti.post("/launch")
def launch():
    """
    Canvas/Moodle POST an id_token (JWT) here.
    We:
      1) Parse (dev: without verifying signature)
      2) Branch by message_type
         - LtiDeepLinkingRequest -> save settings -> /deep-link/picker
         - LtiResourceLinkRequest -> normal assignment launch -> /grader
    """
    if jwt is None:
        return "PyJWT not installed (add PyJWT to requirements.txt).", 500

    id_token = request.form.get("id_token") or ""
    if not id_token:
        return "Missing id_token", 400

    # DEV MODE decode (no signature verification). DO NOT ship this as-is for prod.
    try:
        claims = jwt.decode(id_token, options={"verify_signature": False, "verify_aud": False})
    except Exception as e:
        _log(f"JWT decode error: {e}")
        return "Invalid id_token", 400

    # Log the essentials for troubleshooting
    msg_type     = claims.get(LTI_CLAIM_MSG_TYPE)
    version      = claims.get(LTI_CLAIM_VERSION)
    deployment   = claims.get(LTI_CLAIM_DEPLOY)
    custom       = claims.get(LTI_CLAIM_CUSTOM) or {}
    aud          = claims.get("aud")  # Canvas client_id
    sub          = claims.get("sub")
    roles        = claims.get("https://purl.imsglobal.org/spec/lti/claim/roles", [])
    context      = claims.get("https://purl.imsglobal.org/spec/lti/claim/context", {}) or {}

    _log(f"message_type={msg_type}, version={version}, deployment_id={deployment}, aud={aud}")
    _log(f"roles={roles}")
    _log(f"context={context}")
    _log(f"custom={custom}")

    # Make some basic session info available to downstream routes/templates
    session["user_id"]          = sub or session.get("user_id") or "lti_user"
    session["roles"]            = roles or session.get("roles") or []
    session["lti_version"]      = version
    session["deployment_id"]    = deployment
    session["oidc_client_id"]   = session.get("oidc_client_id") or (aud if isinstance(aud, str) else (aud[0] if isinstance(aud, list) and aud else None))
    session["course_id"]        = context.get("id") or session.get("course_id")
    session["course_label"]     = context.get("label") or session.get("course_label")

    # ---- Branch: Deep Linking picker ----
    if msg_type == "LtiDeepLinkingRequest":
        dl = claims.get(LTI_DL_SETTINGS) or {}
        deep_link_return_url = dl.get("deep_link_return_url")
        session["deep_link_return_url"] = deep_link_return_url
        _log(f"DeepLinkingRequest: return_url={deep_link_return_url}")
        return redirect(url_for("lti.deep_link_picker"))

    # ---- Branch: Normal ResourceLink (open the assignment) ----
    if msg_type in ("LtiResourceLinkRequest", None):
        # If your LMS passes your assignment identity via custom field:
        rubiqs_slug = (custom.get("rubiqs_slug") or "").strip()
        if not rubiqs_slug:
            # Fallback: allow querystring for manual testing
            rubiqs_slug = (request.args.get("rubiqs_slug") or "").strip()

        if rubiqs_slug:
            session["rubiqs_slug"] = rubiqs_slug
            _log(f"ResourceLinkRequest -> slug={rubiqs_slug}")

        # If you want to land students directly in your assignment experience,
        # either render a student view route or go to a central hub.
        # For now, send them to the Grader home; your student flow can pick up session["rubiqs_slug"].
        return redirect(url_for("lti.grader_base"))

    # Unknown/unsupported type
    return f"Unsupported LTI message_type: {msg_type}", 400
