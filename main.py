# main.py  —  Rubiqs Grader–only entrypoint

from dotenv import load_dotenv, find_dotenv

# Load .env from project root, overriding shell vars if needed
load_dotenv(find_dotenv(usecwd=True), override=True)
print("[boot] .env path:", find_dotenv(usecwd=True))

import os
from datetime import timedelta

from flask import Flask, render_template, request, redirect, session, url_for
from flask_session import Session
from flask_session.sessions import FileSystemSessionInterface

# === Define paths and create app FIRST ===
project_root = os.path.abspath(os.path.dirname(__file__))
static_dir = os.path.join(project_root, "static")
template_dir = os.path.join(project_root, "templates")

app = Flask(
    __name__,
    static_folder=static_dir,
    static_url_path="/static",
    template_folder=template_dir,
)

# === Secrets / Session basics ===
app.secret_key = os.getenv("FLASK_SECRET", "dev-key")
app.permanent_session_lifetime = timedelta(days=7)

app.config.update(
    {
        "SESSION_TYPE": "filesystem",
        "SESSION_FILE_DIR": "./.flask_session",
        "SESSION_COOKIE_NAME": "lti_session",
        "SESSION_PERMANENT": False,
        "SESSION_USE_SIGNER": False,
        "SESSION_COOKIE_SAMESITE": "None",
        "SESSION_COOKIE_SECURE": True,  # flipped to False in dev toggle below
        "TINYMCE_API_KEY": os.getenv("TINYMCE_API_KEY"),
        "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY"),
    }
)

# --- Optional dev toggle so local HTTP can set cookies without Secure flag ---
is_dev = os.getenv("FLASK_ENV") == "development" or os.getenv("DEV_INSECURE_COOKIES") == "1"
if is_dev:
    app.config["SESSION_COOKIE_SECURE"] = False

# === Make has_tool available to all templates ===
from app.utils.auth_decorators import has_tool  # keep if grader_base.html checks tool access
app.jinja_env.globals.update(has_tool=has_tool)

# === Supabase client on app config (for blueprints to use) ===
from app.supabase_client import supabase as supabase_client
app.config["SUPABASE"] = supabase_client
print("✅ app.config['SUPABASE'] attached:", bool(app.config.get("SUPABASE")))

# === Custom session interface to set cookie explicitly (with SameSite=None) ===
class SafeSessionInterface(FileSystemSessionInterface):
    def __init__(self, cache_dir, threshold, mode, key_prefix):
        super().__init__(
            cache_dir=cache_dir, threshold=threshold, mode=mode, key_prefix=key_prefix
        )

    def save_session(self, app, session, response):
        session_id = getattr(session, "sid", None)
        if isinstance(session_id, bytes):
            session_id = session_id.decode("utf-8")
        response.set_cookie(
            app.config["SESSION_COOKIE_NAME"],
            session_id,
            httponly=True,
            secure=bool(app.config.get("SESSION_COOKIE_SECURE", True)),
            samesite=app.config.get("SESSION_COOKIE_SAMESITE", "None"),
            path="/",
        )

app.session_interface = SafeSessionInterface(
    cache_dir=app.config["SESSION_FILE_DIR"], threshold=500, mode=0o600, key_prefix=""
)
Session(app)

# === ROUTE WIRING (Grader-only) ===
# 1) Import the shared LTI blueprint object
from app.routes import lti  # Blueprint named "lti"

# 2) Import ONLY the modules that define @lti.route(...) for LTI core + Auth + Grader
def _safe_import_routes():
    import importlib, traceback

    modules = [
        # LTI core (launch, jwks, oidc login, AGS helpers, etc.)
        "app.routes.lti_core",
        # Auth (manual login, public signup, logout, etc.)
        "app.routes.auth",
        # Grader (grader_base page, assignments, submissions, review, grade-docx, grade-uscis-form, etc.)
        "app.routes.grader",
    ]
    loaded = []
    for m in modules:
        try:
            importlib.import_module(m)
            loaded.append(m)
        except Exception as e:
            print(f"❌ Failed importing routes module: {m}\n{e}\n{traceback.format_exc()}")
    print("✅ Loaded route modules:", loaded)

_safe_import_routes()

# 3) Register the LTI blueprint (no url_prefix → routes keep their declared paths)
if "lti" not in app.blueprints:
    app.register_blueprint(lti)
    print("✅ Registered blueprint: lti")
else:
    print("ℹ️ Blueprint 'lti' already registered")

# ---------- Minimal test/dev & diagnostics ----------
@app.before_request
def log_every_request():
    print(f"📥 {request.method} {request.path}")

@app.route("/")
def index():
    # You can redirect to your LTI dashboard or show a simple “live” message
    return "🚀 Rubiqs Grader LTI is live!"

@app.route("/health")
def health():
    return {"ok": True}

# === Cookie settings finalization & diagnostics ===
app.config.update(
    SESSION_COOKIE_NAME="lti_session",
    SESSION_COOKIE_SAMESITE="None",  # exact casing
    SESSION_COOKIE_SECURE=app.config.get("SESSION_COOKIE_SECURE", True),
)
app.config.setdefault("SESSION_TYPE", "filesystem")
app.config.setdefault("SESSION_PERMANENT", True)

# --- quick endpoint sanity checks (Grader-only) ---
def _assert_endpoint(ep: str):
    endpoints = {rule.endpoint for rule in app.url_map.iter_rules()}
    if ep in endpoints:
        print(f"✅ endpoint ok: {ep}")
    else:
        print(f"⚠️ missing endpoint: {ep}")

for ep in [
    "lti.launch",               # POST /launch
    "lti.grader_base",          # GET /grader
    "lti.rubiqs_suite_login",   # GET/POST /rubiqs-suite-login
    "lti.public_signup",        # GET/POST /public-signup
    "lti.logout",
    "lti.unauthorized",
]:
    _assert_endpoint(ep)

print("\n-- Registered blueprints --")
for name in app.blueprints:
    print(" •", name)

print("\n-- URL map --")
print(app.url_map)

# === Launch ===
if __name__ == "__main__":
    os.environ.setdefault("PYTHONUNBUFFERED", "1")
    # NOTE: Server binds to port 5050 (matches your previous setup)
    app.run(host="0.0.0.0", port=5050, debug=True)
