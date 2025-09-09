# app/routes/lti_deep_link.py
import os, time, json
from urllib.parse import urlparse
from flask import request, session, render_template_string, redirect, url_for
from app.routes import lti
from app.supabase_client import supabase
import jwt  # PyJWT

# helper: issue a Deep Linking Response JWT back to Canvas
def _deep_link_response_jwt(audience, deployment_id, deep_link_return_url, content_items, tool_private_key_pem, kid=None):
    now = int(time.time())
    payload = {
        "iss": os.getenv("LTI_ISSUER_TOOL") or "https://rubiqs-grader",  # your tool identifier
        "aud": audience,                      # Canvas client_id
        "iat": now,
        "exp": now + 300,
        "nonce": str(now),
        "https://purl.imsglobal.org/spec/lti/claim/deployment_id": deployment_id,
        "https://purl.imsglobal.org/spec/lti-dl/claim/content_items": content_items,
        "https://purl.imsglobal.org/spec/lti-dl/claim/msg": "Rubiqs content selected.",
        "https://purl.imsglobal.org/spec/lti-dl/claim/errormsg": None,
    }
    headers = {"kid": kid} if kid else {}
    return jwt.encode(payload, tool_private_key_pem, algorithm="RS256", headers=headers)

# 1) After /launch identifies a DeepLinkingRequest, send user here
@lti.route("/deep-link/picker", methods=["GET"])
def deep_link_picker():
    # Expect these were put into session by /launch when message_type==DeepLinkingRequest
    deep_link_return_url = session.get("deep_link_return_url")
    client_id            = session.get("oidc_client_id")  # platform client_id (your audience)
    deployment_id        = session.get("deployment_id")

    if not all([deep_link_return_url, client_id, deployment_id]):
        return "Deep linking context missing.", 400

    # Pull a lightweight list of assignments to pick from
    rows = supabase.table("grader_assignments").select(
        "id, display_title, assignment_title, slug, total_points, gpt_model"
    ).order("created_at", desc=True).limit(100).execute().data or []

    # Simple inline template (use real Jinja template later if you want)
    html = """
    <!doctype html>
    <html><head><meta charset="utf-8"><title>Rubiqs – Select Content</title>
    <style>
      body { font-family: system-ui, -apple-system, Segoe UI, Roboto, sans-serif; padding: 1.5rem; }
      table { width: 100%; border-collapse: collapse; }
      th, td { padding: .5rem .6rem; border-bottom: 1px solid #eee; text-align: left; }
      button { padding: .4rem .8rem; border: 0; background:#1f3a54; color:#fff; border-radius: 8px; cursor:pointer; }
      button:hover { background:#163148; }
      .muted { color:#666; font-size:.9rem; }
    </style></head><body>
    <h2>Select a Rubiqs Grader Assignment</h2>
    <p class="muted">This will insert an LTI link into your Canvas page with the selected assignment.</p>
    <table>
      <thead><tr><th>Title</th><th>Slug</th><th>Points</th><th>Model</th><th></th></tr></thead>
      <tbody>
        {% for a in rows %}
        <tr>
          <td>{{ (a.display_title or a.assignment_title) or "Untitled" }}</td>
          <td>{{ a.slug or "" }}</td>
          <td>{{ a.total_points or "—" }}</td>
          <td>{{ a.gpt_model or "—" }}</td>
          <td>
            <form method="POST" action="{{ url_for('lti.deep_link_submit') }}">
              <input type="hidden" name="slug" value="{{ a.slug or '' }}">
              <input type="hidden" name="display_title" value="{{ (a.display_title or a.assignment_title) or 'Rubiqs Assignment' }}">
              <button type="submit">Insert</button>
            </form>
          </td>
        </tr>
        {% endfor %}
      </tbody>
    </table>
    </body></html>
    """
    return render_template_string(html, rows=rows)

# 2) Build & POST Deep Linking Response
@lti.route("/deep-link/submit", methods=["POST"])
def deep_link_submit():
    deep_link_return_url = session.get("deep_link_return_url")
    client_id            = session.get("oidc_client_id")
    deployment_id        = session.get("deployment_id")
    tool_kid             = os.getenv("LTI_TOOL_KID")  # if you publish JWKs, include kid
    private_key_pem      = os.getenv("LTI_TOOL_PRIVATE_KEY_PEM")

    if not all([deep_link_return_url, client_id, deployment_id, private_key_pem]):
        return "Deep linking configuration missing.", 400

    slug         = (request.form.get("slug") or "").strip()
    display_name = (request.form.get("display_title") or "Rubiqs Assignment").strip()

    # This is the LTI ResourceLink Canvas will insert
    launch_url = os.getenv("TOOL_LAUNCH_URL") or (request.host_url.rstrip("/") + "/launch")

    # One content_item with custom params
    content_item = {
      "type": "ltiResourceLink",
      "title": display_name,
      "url": launch_url,
      "presentation": {"documentTarget": "iframe"},
      "custom": {
        "rubiqs_slug": slug,
        # (optional) "rubiqs_link_title": display_name
      }
    }

    id_token = _deep_link_response_jwt(
        audience=client_id,
        deployment_id=deployment_id,
        deep_link_return_url=deep_link_return_url,
        content_items=[content_item],
        tool_private_key_pem=private_key_pem,
        kid=tool_kid
    )

    # Per spec: POST a form with "JWT" back to deep_link_return_url
    form_html = f"""
    <html><body onload="document.forms[0].submit()">
      <form action="{deep_link_return_url}" method="POST">
        <input type="hidden" name="JWT" value="{id_token}">
        <noscript><button type="submit">Return to LMS</button></noscript>
      </form>
    </body></html>
    """
    return form_html
