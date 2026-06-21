"""Tutor Form Filler — local web app (Flask backend).

Run:  python server.py
Opens a modern dark-themed UI in your browser. All data stays on your machine.
"""

from __future__ import annotations

import os
import threading
import webbrowser
from datetime import datetime

from flask import Flask, jsonify, request, send_file, render_template

from tff import config, storage
from tff.docx_writer import build_timesheet
from tff.models import (
    Session,
    computed_hours,
    display_to_iso,
    format_hours,
    iso_to_display,
    sessions_for_month,
)

app = Flask(__name__, static_folder="static", template_folder="templates")
# Always serve the latest templates/static from disk (no stale cached page
# after an update; just refresh the browser).
app.config["TEMPLATES_AUTO_RELOAD"] = True
app.config["SEND_FILE_MAX_AGE_DEFAULT"] = 0
app.jinja_env.auto_reload = True

HOST = "127.0.0.1"
PORT = 5000


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------
def _session_to_json(s: Session) -> dict:
    return {
        "id": s.id,
        "date": s.date,
        "date_display": s.display_date(),
        "course_code": s.course_code,
        "activity": s.activity,
        "time_started": s.time_started,
        "time_ended": s.time_ended,
        "total_hours_override": s.total_hours_override,
        "hours": s.effective_hours(),
        "year": s.year,
        "month": s.month,
    }


def _parse_payload(data: dict) -> Session:
    """Build a Session from incoming JSON, validating and normalizing."""
    date_raw = (data.get("date") or "").strip()
    # accept both ISO and DD/MM/YYYY
    try:
        iso = display_to_iso(date_raw) if "/" in date_raw else date_raw
        iso_to_display(iso)  # validates ISO
    except ValueError:
        raise ValueError("Date must be DD/MM/YYYY, e.g. 02/03/2026.")

    course = (data.get("course_code") or "").strip()
    if not course:
        raise ValueError("Please choose or enter a course code.")
    activity = (data.get("activity") or "").strip()
    if not activity:
        raise ValueError("Please choose an activity.")

    for label, key in (("started", "time_started"), ("ended", "time_ended")):
        val = (data.get(key) or "").strip()
        try:
            datetime.strptime(val, "%H:%M")
        except ValueError:
            raise ValueError(f"Time {label} must be HH:MM (24-hour), e.g. 14:00.")

    override = data.get("total_hours_override")
    if override in ("", None):
        override = None
    else:
        try:
            override = float(override)
        except (TypeError, ValueError):
            raise ValueError("Override hours must be a number, e.g. 1.5.")

    kwargs = dict(
        date=iso,
        course_code=course,
        activity=activity,
        time_started=data["time_started"].strip(),
        time_ended=data["time_ended"].strip(),
        total_hours_override=override,
    )
    if data.get("id"):
        kwargs["id"] = data["id"]
    return Session(**kwargs)


# --------------------------------------------------------------------------
# Page
# --------------------------------------------------------------------------
@app.route("/")
def index():
    return render_template("index.html")


# --------------------------------------------------------------------------
# Sessions API
# --------------------------------------------------------------------------
@app.route("/api/sessions", methods=["GET"])
def list_sessions():
    sessions = storage.load_sessions()
    sessions.sort(key=lambda s: (s.date, s.time_started))
    return jsonify([_session_to_json(s) for s in sessions])


@app.route("/api/sessions", methods=["POST"])
def create_session():
    try:
        session = _parse_payload(request.get_json(force=True))
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    sessions = storage.load_sessions()
    sessions.append(session)
    storage.save_sessions(sessions)
    return jsonify(_session_to_json(session)), 201


@app.route("/api/sessions/<sid>", methods=["PUT"])
def update_session(sid):
    payload = request.get_json(force=True)
    payload["id"] = sid
    try:
        updated = _parse_payload(payload)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    sessions = storage.load_sessions()
    for i, s in enumerate(sessions):
        if s.id == sid:
            sessions[i] = updated
            storage.save_sessions(sessions)
            return jsonify(_session_to_json(updated))
    return jsonify({"error": "Session not found."}), 404


@app.route("/api/sessions/<sid>", methods=["DELETE"])
def delete_session(sid):
    sessions = storage.load_sessions()
    remaining = [s for s in sessions if s.id != sid]
    if len(remaining) == len(sessions):
        return jsonify({"error": "Session not found."}), 404
    storage.save_sessions(remaining)
    return jsonify({"ok": True})


@app.route("/api/hours", methods=["GET"])
def hours():
    start = request.args.get("start", "")
    end = request.args.get("end", "")
    return jsonify({"hours": format_hours(computed_hours(start, end))})


# --------------------------------------------------------------------------
# Settings API
# --------------------------------------------------------------------------
@app.route("/api/settings", methods=["GET"])
def get_settings():
    s = storage.load_settings()
    return jsonify({
        "student_name": s.get("student_name", ""),
        "student_no": s.get("student_no", ""),
        "school": s.get("school", ""),
        "logo_path": s.get("logo_path", ""),
        "logo_width_cm": s.get("logo_width_cm", 4.3),
        "course_codes": s.get("course_codes", config.DEFAULT_COURSE_CODES),
        "activities": s.get("activities", config.DEFAULT_ACTIVITIES),
        "logo_exists": os.path.exists(config.resolve_logo_path(s)),
    })


@app.route("/api/settings", methods=["POST"])
def save_settings_route():
    data = request.get_json(force=True)
    settings = storage.load_settings()
    settings["student_name"] = (data.get("student_name") or "").strip()
    settings["student_no"] = (data.get("student_no") or "").strip()
    settings["school"] = (data.get("school") or "").strip()
    settings["logo_path"] = (data.get("logo_path") or "").strip()
    try:
        settings["logo_width_cm"] = float(data.get("logo_width_cm", 4.3))
    except (TypeError, ValueError):
        return jsonify({"error": "Logo width must be a number."}), 400
    codes = data.get("course_codes", [])
    if isinstance(codes, str):
        codes = [c.strip() for c in codes.replace(",", "\n").splitlines()]
    settings["course_codes"] = [c.strip() for c in codes if c and c.strip()]
    storage.save_settings(settings)
    return jsonify({"ok": True})


# --------------------------------------------------------------------------
# Form generation
# --------------------------------------------------------------------------
@app.route("/api/generate", methods=["POST"])
def generate():
    data = request.get_json(force=True)
    try:
        month_num = int(data.get("month"))
        year = int(data.get("year"))
    except (TypeError, ValueError):
        return jsonify({"error": "Invalid month or year."}), 400
    if not 1 <= month_num <= 12:
        return jsonify({"error": "Invalid month."}), 400

    sessions = storage.load_sessions()
    subset = sessions_for_month(sessions, year, month_num)
    if not subset:
        month_name = config.MONTHS[month_num - 1]
        return jsonify(
            {"error": f"No sessions recorded for {month_name} {year}."}), 400

    settings = storage.load_settings()
    month_name = config.MONTHS[month_num - 1]
    out_path = os.path.join(
        config.OUTPUT_DIR, f"Timesheet_{month_name}_{year}.docx")
    try:
        build_timesheet(subset, settings, month_name, out_path)
    except Exception as exc:  # noqa: BLE001
        return jsonify({"error": str(exc)}), 500

    logo_ok = os.path.exists(config.resolve_logo_path(settings))
    return jsonify({
        "ok": True,
        "filename": os.path.basename(out_path),
        "logo_warning": not logo_ok,
        "count": len(subset),
    })


@app.route("/api/download/<month>/<int:year>", methods=["GET"])
def download(month, year):
    out_path = os.path.join(config.OUTPUT_DIR, f"Timesheet_{month}_{year}.docx")
    if not os.path.exists(out_path):
        return jsonify({"error": "File not found."}), 404
    return send_file(out_path, as_attachment=True,
                     download_name=os.path.basename(out_path))


def _open_browser():
    webbrowser.open(f"http://{HOST}:{PORT}/")


if __name__ == "__main__":
    storage._ensure_dirs()
    # open the browser shortly after the server starts
    if not os.environ.get("WERKZEUG_RUN_MAIN"):
        threading.Timer(1.0, _open_browser).start()
    app.run(host=HOST, port=PORT, debug=False)
