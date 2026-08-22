import hmac
import os
import re
import secrets
import tempfile
import threading
import time
import uuid
from datetime import timedelta
from urllib.parse import urljoin, urlparse

from flasgger import Swagger
from flask import (
    Flask,
    jsonify,
    redirect,
    render_template,
    request,
    send_file,
    session,
    url_for,
)
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from werkzeug.middleware.proxy_fix import ProxyFix

from app.pipelines.feedback_gen_pipeline import doc_analysis_pipeline
from app.services.acronym_store import (
    add_acronym,
    load_acronyms,
    remove_acronym,
)
from app.services.body_llm_edits import build_body_edit_plan
from app.services.document_analysis_services import load_paragraphs, word_count
from app.services.jutlp_articles import get_jutlp_articles
from app.services.language_corrections import summarize_spelling_correction_repeats
from app.services.output_filename import build_output_filename
from app.services.output_generation_samfix import (
    build_abstract_check_plan,
    build_author_check_plan,
    build_citation_check_plan,
    build_document_body_check_plan,
    build_edited_document,
    build_keywords_check_plan,
    build_title_check_plan,
)

app = Flask(__name__, template_folder="templates", static_folder="static")

# Trust X-Forwarded-* headers from Railway's load balancer so request.remote_addr
# reflects the real client IP (needed for accurate per-IP rate limiting).
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

# Cap upload size to protect threads from being held by huge files.
# Override via MAX_UPLOAD_MB env var if needed.
_max_upload_mb = int(os.environ.get("MAX_UPLOAD_MB", "16"))
app.config["MAX_CONTENT_LENGTH"] = _max_upload_mb * 1024 * 1024

# Reject manuscripts whose whole-document word count exceeds this limit before
# any pipeline work begins. Override via MAX_WORD_COUNT.
_max_word_count = int(os.environ.get("MAX_WORD_COUNT", "10000"))

# Hard ceiling on how long the whole analysis may run. A document that hasn't
# finished within this many seconds is abandoned and the session marked
# "timeout", freeing the worker. Override via ANALYSIS_TIMEOUT_SECONDS.
_analysis_timeout_seconds = int(os.environ.get("ANALYSIS_TIMEOUT_SECONDS", "600"))
_timeout_message = (
    f"Analysis exceeded the {max(1, _analysis_timeout_seconds // 60)}-minute "
    "time limit and was stopped. The document may be very large or complex — "
    "try shortening it and submitting again."
)

# CORS: only enabled when CORS_ALLOWED_ORIGINS env var is set (comma-separated).
# Without it, browsers will block cross-origin calls from e.g. an OAPA WordPress
# page. Set this in Railway to the OAPA site origin(s) when integrating.
_cors_origins = [
    o.strip()
    for o in os.environ.get("CORS_ALLOWED_ORIGINS", "").split(",")
    if o.strip()
]
if _cors_origins:
    CORS(app, resources={r"/api/*": {"origins": _cors_origins}})

# Rate limiting: in-memory storage works because we run a single gunicorn worker
# (see Procfile). If we ever scale to multiple workers, switch storage_uri to
# Redis. Default limits apply to every endpoint; expensive endpoints get
# stricter per-route limits via @limiter.limit decorators below.
_default_limits = os.environ.get("RATE_LIMIT_DEFAULT", "200 per day; 60 per hour").split(";")
_default_limits = [s.strip() for s in _default_limits if s.strip()]
limiter = Limiter(
    key_func=get_remote_address,
    app=app,
    default_limits=_default_limits,
    storage_uri="memory://",
    strategy="fixed-window",
)
_upload_limit = os.environ.get("RATE_LIMIT_UPLOAD", "10 per hour")

# Shared-password authentication. APP_PASSWORD is set by the client (Joey) in
# the Railway dashboard. Setting/changing it triggers a Railway restart and the
# new password is live within ~30s. SECRET_KEY signs session cookies; if not
# set we generate an ephemeral one (means cookies invalidate on every restart,
# which is fine for dev but for prod set a stable value in Railway).
APP_PASSWORD = os.environ.get("APP_PASSWORD", "")
app.secret_key = os.environ.get("SECRET_KEY") or secrets.token_hex(32)
app.permanent_session_lifetime = timedelta(days=7)
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "None"
app.config["SESSION_COOKIE_SECURE"] = (
    os.environ.get("FLASK_ENV", "production") != "development"
)

# Paths that bypass the auth gate. Swagger UI + its assets stay public so
# devs can read the API spec without logging in. /static/* must stay public
# so the login page itself can load CSS/JS.
_PUBLIC_PATH_PREFIXES = (
    "/login",
    "/logout",
    "/apidocs",
    "/apispec",
    "/flasgger_static",
    "/static",
)


def _is_safe_redirect(target: str) -> bool:
    """Reject open redirects: only same-origin paths are allowed."""
    if not target:
        return False
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ("http", "https") and ref_url.netloc == test_url.netloc


@app.before_request
def _require_login():
    if not APP_PASSWORD:
        # Auth disabled when no password is configured (local dev convenience).
        return
    path = request.path
    for prefix in _PUBLIC_PATH_PREFIXES:
        if path == prefix or path.startswith(prefix + "/") or path == prefix + "/":
            return
    if session.get("authed"):
        return
    return redirect(url_for("login_form", next=request.full_path))


@app.get("/login")
def login_form():
    if not APP_PASSWORD:
        return redirect("/")
    if session.get("authed"):
        return redirect("/")
    next_url = request.args.get("next", "/") or "/"
    return render_template("login.html", error=None, next_url=next_url)


@app.post("/login")
@limiter.limit("5 per minute")
def login_submit():
    if not APP_PASSWORD:
        return redirect("/")
    submitted = request.form.get("password", "")
    next_url = request.form.get("next") or "/"
    if not _is_safe_redirect(next_url):
        next_url = "/"
    if hmac.compare_digest(submitted, APP_PASSWORD):
        session.clear()
        session["authed"] = True
        session.permanent = True
        return redirect(next_url)
    return render_template(
        "login.html",
        error="Incorrect access code. Please try again.",
        next_url=next_url,
    ), 401


@app.get("/logout")
def logout():
    session.clear()
    return redirect(url_for("login_form"))


@app.errorhandler(429)
def _ratelimit_handler(e):
    return jsonify({
        "error": "Rate limit exceeded",
        "detail": str(e.description),
    }), 429


@app.errorhandler(413)
def _too_large_handler(e):
    return jsonify({
        "error": "File too large",
        "detail": f"Maximum upload size is {_max_upload_mb} MB.",
    }), 413

app.config["SWAGGER"] = {
    "title": "copy-editor-ai API",
    "uiversion": 3,
    "openapi": "3.0.2",
    "specs_route": "/apidocs/",
}
swagger = Swagger(
    app,
    template={
        "openapi": "3.0.2",
        "info": {
            "title": "copy-editor-ai API",
            "description": (
                "HTTP API for the copy-editor-ai Flask service. Accepts "
                ".docx uploads, runs the editorial analysis pipeline, and "
                "returns structured feedback plus a reviewed document."
            ),
            "version": "0.1.0",
        },
        "tags": [
            {"name": "Analysis", "description": "Upload and analyse documents."},
            {"name": "Results", "description": "Retrieve analysis output and download reviewed documents."},
        ],
    },
)

_sessions: dict = {}


class ProcessingCancelled(Exception):
    pass


class ProcessingTimeout(Exception):
    pass


def _document_word_count(path: str) -> int:
    """Total word count across every paragraph (whole-document count)."""
    return sum(word_count(p.text or "") for p in load_paragraphs(path))


def _build_cli_analysis(input_path: str) -> dict:
    from app.services.editorial_review_comments import build_editorial_review_comment_plan
    editorial_review_plan = build_editorial_review_comment_plan(input_path)

    return {
        "title_plan":           build_title_check_plan(input_path),
        "author_plan":          build_author_check_plan(input_path),
        "abstract_plan":        build_abstract_check_plan(input_path),
        "keywords_plan":        build_keywords_check_plan(input_path),
        "citation_plan":        build_citation_check_plan(input_path),
        "document_body_plan":   build_document_body_check_plan(input_path),
        "body_edit_plan":       build_body_edit_plan(input_path),
        "editorial_review_plan": editorial_review_plan,
    }


def _plan_items(label: str, plan: dict) -> list[dict]:
    items = []
    message = (plan.get("message") or "").strip()
    if message:
        items.append({"section": label, "action": plan.get("action", "none"),
                      "reason": plan.get("reason", ""), "message": message})
    for comment in plan.get("comments", []):
        comment_message = (comment.get("message") or "").strip()
        if comment_message:
            items.append({"section": label, "action": plan.get("action", "none"),
                          "reason": plan.get("reason", ""), "message": comment_message})
    return items


def _body_edit_items(label: str, plan: dict) -> list[dict]:
    items = []
    for edit in plan.get("edits", []) or []:
        find_text = (edit.get("find") or "").strip()
        replace_text = (edit.get("replace") or "").strip()
        reason = (edit.get("reason") or "").strip()
        if not find_text or not replace_text:
            continue
        message = f'"{find_text}" \u2192 "{replace_text}"'
        if reason:
            message += f" \u2014 {reason}"
        items.append({"section": label, "action": plan.get("action", "none"),
                      "reason": reason, "message": message})
    return items


def _build_cli_frontend_payload(filename: str, plans: dict) -> dict:
    body_edit_plan = plans.get("body_edit_plan") or {"action": "none", "edits": []}
    editorial_review_plan = plans.get("editorial_review_plan") or {"action": "none", "comments": []}

    plan_order = [
        ("Title",                    plans["title_plan"],         _plan_items),
        ("Author",                   plans["author_plan"],         _plan_items),
        ("Abstract",                 plans["abstract_plan"],       _plan_items),
        ("Keywords",                 plans["keywords_plan"],       _plan_items),
        ("Citation",                 plans["citation_plan"],       _plan_items),
        ("Document Body",            plans["document_body_plan"],  _plan_items),
        ("Body copy-edits (tracked)", body_edit_plan,             _body_edit_items),
        ("Editorial review (LLM)",   editorial_review_plan,        _plan_items),
    ]
    sections = []
    issues = []
    for label, plan, item_fn in plan_order:
        items = item_fn(label, plan)
        sections.append({"label": label, "action": plan.get("action", "none"),
                         "reason": plan.get("reason", ""), "count": len(items), "items": items})
        issues.extend(items)
    return {
        "filename": filename,
        "sections": sections,
        "issues": issues,
        "total_issues": len(issues),
        "total_notes": len(issues),
        "high_priority": plans["document_body_plan"].get("action") != "none",
        "categories": {
            "Structure": len(_plan_items("Document Body", plans["document_body_plan"])),
            "Front Page": sum(len(_plan_items(label, plans[key])) for label, key in [
                ("Title", "title_plan"), ("Author", "author_plan"),
                ("Abstract", "abstract_plan"), ("Keywords", "keywords_plan"),
                ("Citation", "citation_plan"),
            ]),
            "Style": len(_body_edit_items("Body copy-edits (tracked)", body_edit_plan)),
            "References": 0,
        },
        "ref_verifications": [],
        "raw_plans": plans,
    }


def _llm_notes_to_results(llm_result) -> list[dict]:
    if llm_result is None:
        return []

    notes = getattr(llm_result, "notes", []) or []
    results = []

    for i, note in enumerate(notes, start=1):
        severity = str(getattr(note, "severity", "")).lower()
        if severity in ("high", "requires_attention"):
            status = "fail"
        elif severity in ("medium", "advisory"):
            status = "warn"
        else:
            continue

        message = str(getattr(note, "message", "")).strip()
        suggestion = str(getattr(note, "suggestion", "")).strip()
        if suggestion:
            message = f"{message} Suggested fix: {suggestion}"

        # Pass the section through to the frontend so the editorial-notes
        # panel can group items by paper section (Introduction, Methods, …).
        section = str(getattr(note, "section", "") or "").strip()

        results.append(
            {
                "rule_id": f"LLM{i:03d}",
                "status": status,
                "message": message,
                "section": section,
            }
        )

    return results


def _sam_plan_to_issues(sam_result: dict | None) -> list[dict]:
    """Convert Sam's build_edited_document plan into frontend issue dicts."""
    if not sam_result:
        return []
    plan = sam_result.get("plan", {})
    issues = []

    def _add(rule_id: str, message: str, status: str = "warn", category: str = "Front Page") -> None:
        first_line = (message or "").strip().split("\n")[0].strip()
        if first_line:
            issues.append({
                "rule_id": rule_id,
                "status": status,
                "message": first_line,
                "source": "sam",
                "category": category,
            })

    title = plan.get("title", {})
    if title.get("action", "none") != "none" and title.get("message"):
        _add("SAM_TITLE", title["message"], "warn", "Front Page")

    author = plan.get("author", {})
    if author.get("action", "none") != "none" and author.get("message"):
        _add("SAM_AUTH", author["message"], "fail", "Front Page")

    abstract = plan.get("abstract", {})
    if abstract.get("action", "none") != "none":
        for i, c in enumerate(abstract.get("comments", []), start=1):
            _add(f"SAM_ABS{i:02d}", c.get("message", ""), "warn", "Front Page")

    keywords = plan.get("keywords", {})
    if keywords.get("action", "none") != "none" and keywords.get("message"):
        _add("SAM_KW", keywords["message"], "warn", "Front Page")

    citation = plan.get("citation", {})
    if citation.get("action", "none") != "none" and citation.get("message"):
        _add("SAM_CITE", citation["message"], "warn", "Front Page")

    body = plan.get("document_body", {})
    if body.get("action", "none") != "none":
        for i, c in enumerate(body.get("comments", []), start=1):
            msg = c.get("message", "")
            if not msg.strip():
                continue
            status = "fail" if "missing" in msg.lower() else "warn"
            category = "Structure" if "missing" in msg.lower() else "Style"
            _add(f"SAM_BODY{i:02d}", msg, status, category)

    return issues


def _dedup_sam_issues(sam_issues: list[dict], existing_issues: list[dict]) -> list[dict]:
    """Remove Sam's issues that duplicate existing ones (3+ significant word overlap)."""
    def _words(text: str) -> set[str]:
        return {w for w in re.sub(r"[^a-z0-9 ]", "", text.lower()).split() if len(w) > 3}

    existing_word_sets = [_words(i["message"]) for i in existing_issues]
    deduped = []
    for issue in sam_issues:
        sam_words = _words(issue["message"])
        is_dup = any(len(sam_words & ew) >= 3 for ew in existing_word_sets)
        if not is_dup:
            deduped.append(issue)
    return deduped


@app.get("/")
def index():
    return render_template("index.html")


@app.get("/api/jutlp-articles")
@limiter.limit("30 per hour")
def jutlp_articles_api():
    """
    Return a small rotating feed of published JUTLP articles.
    ---
    tags:
      - Results
    responses:
      200:
        description: Article cards for the processing screen.
    """
    try:
        limit = int(request.args.get("limit", "30"))
    except (TypeError, ValueError):
        limit = 10
    return jsonify({"articles": get_jutlp_articles(limit=limit)})


# ---------------------------------------------------------------------------
# Acronym allow-list admin
#
# The list lives in a JSON file managed by app.services.acronym_store. On
# Railway, set ACRONYM_DB_PATH to a path inside a mounted volume so edits
# survive redeploys; without a volume the file resets to the bundled seed on
# each container restart.
#
# All routes are first gated by the existing shared-password auth via the
# @app.before_request hook (any logged-in user can READ the list — the
# pipeline needs that). Mutating routes (POST/DELETE and the editor page)
# are additionally gated by ACRONYM_ADMIN_PASSWORD when set, so only those
# editors with the second password can change the list. When the env var is
# unset, the second gate is disabled and behaviour matches the original
# single-gate flow.
# ---------------------------------------------------------------------------

ACRONYM_ADMIN_PASSWORD = os.environ.get("ACRONYM_ADMIN_PASSWORD", "")


def _acronym_admin_active() -> bool:
    return bool(ACRONYM_ADMIN_PASSWORD)


def _acronym_admin_authed() -> bool:
    return bool(session.get("acronym_admin"))


def _require_acronym_admin():
    """Return a Flask response if the caller isn't authorised, else None."""
    if not _acronym_admin_active():
        return None
    if _acronym_admin_authed():
        return None
    return jsonify({"error": "Acronym editing is restricted."}), 403


@app.get("/settings/acronyms")
def acronyms_admin_page():
    # When ACRONYM_DB_PATH is set the store is pointed at a path the operator
    # has wired up (typically a Railway volume mount), so edits persist across
    # redeploys. We surface this to the template so the "ephemeral filesystem"
    # warning only appears when persistence isn't configured.
    persistent = bool(os.environ.get("ACRONYM_DB_PATH"))
    return render_template(
        "acronyms.html",
        persistent_storage=persistent,
        admin_required=_acronym_admin_active(),
        admin_authed=_acronym_admin_authed(),
        admin_login_error=None,
    )


@app.post("/settings/acronyms/login")
@limiter.limit("5 per minute")
def acronyms_admin_login():
    if not _acronym_admin_active():
        return redirect(url_for("acronyms_admin_page"))
    submitted = request.form.get("admin_password", "")
    if hmac.compare_digest(submitted, ACRONYM_ADMIN_PASSWORD):
        session["acronym_admin"] = True
        return redirect(url_for("acronyms_admin_page"))
    return render_template(
        "acronyms.html",
        persistent_storage=bool(os.environ.get("ACRONYM_DB_PATH")),
        admin_required=True,
        admin_authed=False,
        admin_login_error="Incorrect editor password.",
    ), 401


@app.post("/settings/acronyms/logout")
def acronyms_admin_logout():
    session.pop("acronym_admin", None)
    return redirect(url_for("acronyms_admin_page"))


@app.get("/api/acronyms")
def list_acronyms_api():
    # Reading the list is unrestricted — the pipeline needs it on every
    # document run, and read-only access doesn't risk corrupting the data.
    return jsonify({"acronyms": load_acronyms()})


@app.post("/api/acronyms")
def add_acronym_api():
    gate = _require_acronym_admin()
    if gate is not None:
        return gate
    data = request.get_json(silent=True) or {}
    key = (data.get("key") or "").strip()
    expansions = data.get("expansions") or []
    if isinstance(expansions, str):
        expansions = [expansions]
    expansions = [str(e).strip() for e in expansions if str(e).strip()]
    if not key:
        return jsonify({"error": "Acronym is required."}), 400
    if not expansions:
        return jsonify({"error": "At least one expansion is required."}), 400
    try:
        updated = add_acronym(key, expansions)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    return jsonify({"acronyms": updated})


@app.delete("/api/acronyms/<path:key>")
def delete_acronym_api(key: str):
    gate = _require_acronym_admin()
    if gate is not None:
        return gate
    updated = remove_acronym(key)
    return jsonify({"acronyms": updated})


@app.post("/api/upload")
@limiter.limit(lambda: _upload_limit)
def upload():
    """
    Upload a .docx manuscript for editorial analysis.
    ---
    tags:
      - Analysis
    consumes:
      - multipart/form-data
    parameters:
      - in: formData
        name: file
        type: file
        required: true
        description: The .docx manuscript to analyse.
    responses:
      200:
        description: Upload accepted, processing started.
        schema:
          type: object
          properties:
            session_id:
              type: string
              example: d83eff1c-1e94-4638-9c4c-801fa3875112
      400:
        description: Bad request (no file or wrong format).
    """
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]
    if not file.filename or not file.filename.endswith(".docx"):
        return jsonify({"error": "Only .docx files are accepted"}), 400

    tmp_dir = tempfile.mkdtemp()
    input_path = os.path.join(tmp_dir, file.filename)
    file.save(input_path)

    # Word-count gate: reject oversized manuscripts before spending any pipeline
    # time on them. Best-effort — if the file can't be parsed here, let the
    # pipeline surface the real error rather than blocking on the count.
    try:
        total_words = _document_word_count(input_path)
    except Exception:
        total_words = None
    if total_words is not None and total_words > _max_word_count:
        return jsonify({
            "error": (
                f"Document is too long ({total_words:,} words). The maximum is "
                f"{_max_word_count:,} words. Please shorten the manuscript and "
                "try again."
            ),
            "word_count": total_words,
            "max_word_count": _max_word_count,
        }), 400

    output_filename = build_output_filename(input_path, tmp_dir)
    output_path = os.path.join(tmp_dir, output_filename)

    session_id = str(uuid.uuid4())
    _sessions[session_id] = {
        "status": "processing",
        "progress": 0,
        "stage": "starting",
        "filename": file.filename,
        "output_filename": output_filename,
        "cancel_requested": False,
    }

    def _run():
        start = time.monotonic()

        def _update_progress(pct, stage):
            session_state = _sessions.get(session_id, {})
            if (
                session_state.get("cancel_requested")
                or session_state.get("status") in ("cancelled", "timeout")
            ):
                raise ProcessingCancelled()
            if time.monotonic() - start > _analysis_timeout_seconds:
                raise ProcessingTimeout()
            try:
                pct = int(float(pct))
            except (TypeError, ValueError):
                return
            pct = max(0, min(99, pct))
            current = int(_sessions[session_id].get("progress", 0) or 0)
            if pct < current:
                pct = current
            _sessions[session_id].update({
                "progress": pct,
                "stage": stage or _sessions[session_id].get("stage", "processing"),
            })

        outcome: dict = {}

        def _pipeline():
            try:
                outcome["result"] = doc_analysis_pipeline(
                    input_path,
                    output_path=output_path,
                    progress_callback=_update_progress,
                )
            except ProcessingTimeout:
                outcome["timeout"] = True
            except ProcessingCancelled:
                outcome["cancelled"] = True
            except Exception as exc:  # noqa: BLE001 — recorded and surfaced below
                outcome["error"] = exc

        try:
            _update_progress(5, "structure")
        except (ProcessingCancelled, ProcessingTimeout):
            return

        # Run the pipeline in its own thread and wait at most the timeout. The
        # cooperative check in _update_progress stops the work at the next
        # progress checkpoint; this join guarantees the user-facing session
        # flips to a final state on time even if the pipeline stalls between
        # checkpoints (e.g. inside a long network call).
        worker = threading.Thread(target=_pipeline, daemon=True)
        worker.start()
        worker.join(_analysis_timeout_seconds)

        if worker.is_alive() or outcome.get("timeout"):
            _sessions[session_id].update({
                "status": "timeout",
                "stage": "timeout",
                # nudge a still-running worker to abort at its next checkpoint
                "cancel_requested": True,
                "error": _timeout_message,
            })
            return

        if outcome.get("cancelled") or _sessions[session_id].get("status") == "cancelled":
            _sessions[session_id].update({
                "status": "cancelled",
                "stage": "cancelled",
                "cancel_requested": True,
            })
            return

        if "error" in outcome:
            _sessions[session_id].update({"status": "error", "error": str(outcome["error"])})
            return

        pipeline_result = outcome["result"]
        if _sessions[session_id].get("cancel_requested"):
            _sessions[session_id].update({"status": "cancelled", "stage": "cancelled"})
            return
        ref_check = pipeline_result["ref_check_result"]

        _sessions[session_id].update({
            "status":                  "done",
            "progress":                100,
            "stage":                   "done",
            "report":                  pipeline_result["deterministic_check_results"],
            "ref_check":               ref_check,
            "ref_results":             ref_check["results"],
            "llm_result":              pipeline_result["llm_result"],
            "sam_result":              pipeline_result.get("sam_result"),
            "spelling_corrections":    pipeline_result.get("spelling_corrections", []),
            "grammar_corrections":     pipeline_result.get("grammar_corrections", []),
            "spell_check_corrections": pipeline_result.get("spell_check_corrections", []),
            "stage_errors":            pipeline_result.get("stage_errors", []),
            "output_path":             output_path,
        })

    threading.Thread(target=_run, daemon=True).start()
    return jsonify({"session_id": session_id})


@app.post("/api/cancel/<session_id>")
@limiter.limit("60 per hour")
def cancel_analysis(session_id):
    session = _sessions.get(session_id)
    if not session:
        return jsonify({"error": "Session not found"}), 404

    if session.get("status") == "processing":
        session.update({
            "status": "cancelled",
            "stage": "cancelled",
            "cancel_requested": True,
        })
        return jsonify({"status": "cancelled"})

    return jsonify({"status": session.get("status", "unknown")})


@app.get("/api/results/<session_id>")
@limiter.limit("600 per hour")
def results(session_id):
    """
    Poll for analysis results.
    ---
    tags:
      - Results
    parameters:
      - in: path
        name: session_id
        type: string
        required: true
        description: Session ID returned by /api/upload.
    responses:
      200:
        description: Analysis complete — returns full report.
        schema:
          type: object
          properties:
            total_notes:   { type: integer }
            high_priority: { type: integer }
            categories:    { type: object }
            issues:        { type: array, items: { type: object } }
            download_url:  { type: string }
            filename:      { type: string }
      202:
        description: Still processing — poll again.
      404:
        description: Session not found.
      500:
        description: Pipeline error.
    """
    session = _sessions.get(session_id)
    if not session:
        return jsonify({"error": "Session not found"}), 404

    if session["status"] == "processing":
        return jsonify({
            "status": "processing",
            "progress": session.get("progress", 0),
            "stage": session.get("stage", ""),
        }), 202

    if session["status"] == "error":
        return jsonify({"error": session.get("error", "Pipeline failed")}), 500

    if session["status"] == "timeout":
        return jsonify({
            "status": "timeout",
            "error": session.get("error", _timeout_message),
        }), 504

    if session["status"] == "cancelled":
        return jsonify({"status": "cancelled", "error": "Processing cancelled"}), 409

    report      = session["report"]
    ref_results = session["ref_results"]
    llm_result           = session.get("llm_result")
    llm_error            = session.get("llm_error")
    sam_result           = session.get("sam_result")
    spelling_corrections    = session.get("spelling_corrections", [])
    grammar_corrections     = session.get("grammar_corrections", [])

    det_results = report["results"]
    llm_mapped  = _llm_notes_to_results(llm_result)

    # ── LLM false-positive overrides ─────────────────────────────────────────
    # Build a lookup of rule_id -> reason for any structural check the LLM
    # identified as a false positive.  These are downgraded from fail → warn.
    fp_overrides: dict[str, str] = {}
    if llm_result and llm_result.structural_validations:
        for sv in llm_result.structural_validations:
            if sv.verdict == "false_positive":
                fp_overrides[sv.rule_id] = sv.reason

    # ── Categories ───────────────────────────────────────────────────────────
    def _det(statuses, *prefixes):
        return sum(
            1 for r in det_results
            if r["status"] in statuses
            and any(r["rule_id"].startswith(p) for p in prefixes)
            and r["rule_id"] not in fp_overrides  # don't count overridden FPs as fails
        )

    # Sam's issues are built after dedup, but we need counts — compute after issues list is final.
    # Placeholder zeros here; updated below after sam_issues are deduped.
    categories = {
        "Structure": (
            _det(("fail",),         "SEC", "MET", "DIS")
            + _det(("fail", "warn"), "SPE", "CON")
            + _det(("fail",),        "FIG", "TAB")
        ),
        "Front Page": (
            _det(("fail", "warn"), "FP")
            + _det(("fail",),       "AFF")
        ),
        "Style":      _det(("fail", "warn"), "STY"),
        "References": sum(
            1 for r in ref_results
            if r["status"] in ("fail", "warn")
            and not r["rule_id"].endswith("_DOI")
            and r["rule_id"] != "REF003"
        ),
        "Editorial": len(llm_mapped),
    }

    # ── Issues list ───────────────────────────────────────────────────────────
    issues = []

    for r in det_results:
        if r["rule_id"] in fp_overrides:
            # LLM flagged as false positive — keep visible but downgrade to warn
            issues.append({
                "rule_id": r["rule_id"],
                "message": (
                    f"{r['message']} "
                    f"[AI review: likely a false positive — {fp_overrides[r['rule_id']]}]"
                ),
                "status": "warn",
                "source": "validator",
            })
        elif r["status"] == "fail":
            issues.append({
                "rule_id": r["rule_id"], "message": r["message"],
                "status": "fail", "source": "validator",
            })
        elif r["status"] == "warn" and (
            r["rule_id"].startswith("SPE")
            or r["rule_id"].startswith("STY")
            or r["rule_id"].startswith("FP01")
            or r["rule_id"] in ("CON001",)
        ):
            issues.append({
                "rule_id": r["rule_id"], "message": r["message"],
                "status": "warn", "source": "validator",
            })

    for r in ref_results:
        # CREF, HREF and CONS rules go exclusively into ref_verifications below —
        # skip here to avoid showing the same entry in two separate sections.
        # REF001 duplicates what SEC008 already reports (References section presence).
        if r["rule_id"].startswith(("CREF", "HREF", "CONS")) or r["rule_id"] in ("REF001", "REF003"):
            continue
        if r["status"] == "fail":
            issues.append({
                "rule_id": r["rule_id"], "message": r["message"],
                "status": "fail", "source": "refs",
            })
        elif (r["status"] == "warn"
              and r["rule_id"].startswith("REFE")
              and not r["rule_id"].endswith("_DOI")):
            issues.append({
                "rule_id": r["rule_id"], "message": r["message"],
                "status": "warn", "source": "refs",
            })

    for r in llm_mapped:
        issues.append({
            "rule_id": r["rule_id"], "message": r["message"],
            "status": r["status"], "source": "llm",
            "section": r.get("section", ""),
        })

    # ── Sam's tracked-changes issues ──────────────────────────────────────────
    sam_issues = _sam_plan_to_issues(sam_result)
    sam_issues = _dedup_sam_issues(sam_issues, issues)
    for r in sam_issues:
        issues.append({
            "rule_id": r["rule_id"], "message": r["message"],
            "status": r["status"], "source": "sam",
        })

    # Add Sam's counts to categories now that dedup is done.
    for r in sam_issues:
        cat = r.get("category", "Front Page")
        if cat in categories:
            categories[cat] += 1

    # ── Ref verifications ─────────────────────────────────────────────────────
    ref_verifications = [
        {"rule_id": r["rule_id"], "status": r["status"], "message": r["message"]}
        for r in ref_results
        if r["rule_id"].startswith(("CREF", "HREF", "CONS")) or r["rule_id"] == "REF003"
    ]

    total_notes  = len(issues)
    high_priority = sum(1 for i in issues if i["status"] == "fail")

    spelling_summary = summarize_spelling_correction_repeats(spelling_corrections)
    language_corrections = (
        [{"type": "spelling", **c} for c in spelling_summary]
        + [{"type": "grammar", **c} for c in grammar_corrections]
    )

    output_filename = session.get("output_filename")
    if not output_filename:
        output_filename = session["filename"].replace(".docx", "_reviewed.docx")

    return jsonify({
        "total_notes":          total_notes,
        "high_priority":        high_priority,
        "categories":           categories,
        "issues":               issues,
        "ref_verifications":    ref_verifications,
        "language_corrections": language_corrections,
        "summary":              _build_summary(issues),
        "download_url":         f"/api/download/{session_id}",
        "filename":             session["filename"],
        "output_filename":      output_filename,
        "llm_available":        llm_result is not None,
        "llm_error":            llm_error,
        "stage_errors":         session.get("stage_errors", []),
    })


@app.post("/api/analyse-cli")
@limiter.limit(lambda: _upload_limit)
def analyse_cli():
    """
    Run CLI-style structural analysis and generate reviewed document.
    ---
    tags:
      - Analysis
    consumes:
      - multipart/form-data
    parameters:
      - in: formData
        name: file
        type: file
        required: true
        description: The .docx manuscript to analyse.
    responses:
      200:
        description: Analysis complete with download URL for reviewed doc.
        schema:
          type: object
          properties:
            filename:     { type: string }
            total_issues: { type: integer }
            sections:     { type: array, items: { type: object } }
            issues:       { type: array, items: { type: object } }
            download_url: { type: string }
      400:
        description: Bad request.
    """
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    file = request.files["file"]
    if not file.filename or not file.filename.endswith(".docx"):
        return jsonify({"error": "Only .docx files are accepted"}), 400

    tmp_dir = tempfile.mkdtemp()
    input_path = os.path.join(tmp_dir, file.filename)
    file.save(input_path)
    output_filename = build_output_filename(input_path, tmp_dir)
    output_path = os.path.join(tmp_dir, output_filename)

    plans = _build_cli_analysis(input_path)
    payload = _build_cli_frontend_payload(file.filename, plans)

    build_edited_document(input_path, output_path)

    session_id = str(uuid.uuid4())
    _sessions[session_id] = {
        "output_path": output_path,
        "filename": file.filename,
        "output_filename": output_filename,
        "mode": "cli",
    }
    payload["download_url"] = f"/api/download/{session_id}"
    payload["output_filename"] = output_filename
    return jsonify(payload)


@app.get("/api/download/<session_id>")
def download(session_id):
    """
    Download the reviewed .docx document.
    ---
    tags:
      - Results
    parameters:
      - in: path
        name: session_id
        type: string
        required: true
        description: Session ID from /api/upload or /api/analyse-cli.
    responses:
      200:
        description: Reviewed Word document as a file download.
        content:
          application/vnd.openxmlformats-officedocument.wordprocessingml.document:
            schema:
              type: string
              format: binary
      404:
        description: Session not found.
    """
    session = _sessions.get(session_id)
    if not session:
        return jsonify({"error": "Session not found"}), 404

    download_name = session.get("output_filename")
    if not download_name:
        download_name = session["filename"].replace(".docx", "_reviewed.docx")

    return send_file(
        session["output_path"],
        as_attachment=True,
        download_name=download_name,
        mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )


def _build_summary(issues: list) -> str:
    fails = [i for i in issues if i["status"] == "fail"]
    warns = [i for i in issues if i["status"] == "warn"]
    if not fails and not warns:
        return "Document passed all checks. No issues found."
    if not fails:
        return f"{len(warns)} suggestion(s) found — no critical issues."
    messages = [i["message"] for i in fails[:3]]
    suffix = f" (+{len(fails) - 3} more)" if len(fails) > 3 else ""
    return "Issues found: " + "; ".join(messages) + suffix


if __name__ == "__main__":
    app.run(debug=True, port=5009)
