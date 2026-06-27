"""Default settings and boilerplate content for the timesheet.

These defaults reproduce the user's example form. Everything here is editable
at runtime via the Settings dialog and persisted to data/settings.json.
"""

from __future__ import annotations

import os

# Project paths -----------------------------------------------------------
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "output")
ASSETS_DIR = os.path.join(PROJECT_ROOT, "assets")

SESSIONS_FILE = os.path.join(DATA_DIR, "sessions.json")
SETTINGS_FILE = os.path.join(DATA_DIR, "settings.json")

DEFAULT_LOGO_PATH = os.path.join(ASSETS_DIR, "wits_logo.png")

MONTHS = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]

# Fixed activity categories (dropdown in the Add/Edit dialog).
DEFAULT_ACTIVITIES = ["Tutoring", "Marking", "Invigilation", "Admin"]

# Placeholder course codes (from the example form) until the real list is
# supplied. Editable in Settings; stored in data/settings.json.
DEFAULT_COURSE_CODES = ["COMS1015A", "COMS1018A", "COMS3007A", "COMS3008A"]

# A red bullet flagged with underline_prefix means that leading prefix
# (e.g. "NB:") is rendered bold + underlined while the rest is bold only.
DEFAULT_BULLETS = [
    {
        "text": "Students must complete all required hours per week for each "
                "teaching block.",
        "underline_prefix": "",
    },
    {
        "text": "NB: Please make sure that you have updated your bank details on "
                "the system with Fees Office before submission date of the first "
                "stipend. Banking details can be updated on the student "
                "self-service portal.",
        "underline_prefix": "NB:",
    },
    {
        "text": "Stipend will not be processed into the Next of kin, Forex or "
                "International bank account.",
        "underline_prefix": "",
    },
    {
        "text": "The last stipend will not be paid out if the student has "
                "outstanding fees after payment of the last stipend is made.",
        "underline_prefix": "",
    },
]

# Each submission-dates row: the ordinal block label is split so the suffix
# can be rendered as superscript. Same for the date's ordinal suffix.
DEFAULT_SUBMISSION_ROWS = [
    {"block_num": "1", "block_suffix": "st", "date_day": "16", "date_suffix": "th",
     "date_rest": " March 2026", "hours": "36 hours"},
    {"block_num": "2", "block_suffix": "nd", "date_day": "15", "date_suffix": "th",
     "date_rest": " May 2026", "hours": "42 hours"},
    {"block_num": "3", "block_suffix": "rd", "date_day": "1", "date_suffix": "st",
     "date_rest": " September 2026", "hours": "42 hours"},
    {"block_num": "4", "block_suffix": "th", "date_day": "23", "date_suffix": "rd",
     "date_rest": " October 2026", "hours": "36 hours"},
]

# Personal fields are blank by default so each tutor fills in their own under
# Settings on first run (their saved data lives in data/settings.json, which is
# git-ignored). The Wits-wide boilerplate below is shared, so it keeps real
# defaults.
DEFAULT_SETTINGS = {
    "student_name": "",
    "student_no": "",
    "school": "",
    "logo_path": "",  # blank -> falls back to assets/wits_logo.png
    "signature_data": "",  # data: URL PNG of the tutor's drawn signature
    "include_signature": False,  # toggle to stamp it in the signature column
    "submission_intro": (
        "The following dates are the due date for submission of timesheets by "
        "the Schools to the FASO office:"
    ),
    "submission_rows": DEFAULT_SUBMISSION_ROWS,
    "bullets": DEFAULT_BULLETS,
    "course_codes": DEFAULT_COURSE_CODES,
    "activities": DEFAULT_ACTIVITIES,
}


def default_settings() -> dict:
    """Return a deep-ish copy of the default settings for safe mutation."""
    import copy
    return copy.deepcopy(DEFAULT_SETTINGS)


def resolve_logo_path(settings: dict) -> str:
    """Logo path from settings, falling back to the bundled crest if blank.

    Keeping the fallback here means an empty 'logo_path' setting still finds
    assets/wits_logo.png, and nothing has to store a machine-specific absolute
    path — so the project stays portable when another tutor clones it.
    """
    path = (settings.get("logo_path") or "").strip()
    return path if path else DEFAULT_LOGO_PATH
