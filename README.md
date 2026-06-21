# Tutor Form Filler (TFF)

I have the software you have not asked for but will want ;)

A small local **web app** for Wits tutors. Record your tutoring
sessions as you go, then at month-end click one button to generate the
**Postgraduate Merit Award Duties Timesheet** as a Word `.docx` that matches the
university's required format.

It runs entirely on your own machine in your browser, nothing is uploaded
anywhere, and no internet connection is required to use it.


---

## What it does

- **Records sessions** — date, course code, activity (Tutoring / Marking /
  Invigilation / Admin), start and end time. Total hours are worked out
  automatically (14:00–17:00 → `3`, 10:00–11:30 → `1.5`), with an optional manual
  override.
- **Stores everything locally** in `data/sessions.json` — survives restarts.
- **Generates the official form** for any month with one click, including all the
  fixed boilerplate (logo, submission-dates table, red NB bullet list).
- **Strict formatting** is handled for you in `tff/docx_writer.py`, so the output
  is consistent every time.

---

## Requirements

- **Windows** (the launcher is a `.bat`; the app itself is cross-platform).
- **Python 3.11 or newer** — get it from <https://python.org> or the Microsoft
  Store. During the Windows installer, tick **“Add Python to PATH”**.

---

## Setup (once)

From the project folder, install the two dependencies:

```
python -m pip install -r requirements.txt
```

That's it — the Wits crest is already bundled at `assets/wits_logo.png`.

---

## Running the app

**Easiest:** double-click **`Run TFF.bat`** (or the *Tutor Form Filler* shortcut
if you created one). A small console window opens and your browser launches at
<http://127.0.0.1:5000>.

**Or from a terminal:**

```
python server.py
```

Keep the console window open while you use the app. To stop it, close that
window or press `Ctrl+C` in it.

### First-time setup inside the app

Open **⚙ Settings** (top-right) and fill in:

- **Student name**, **Student number**, **School** — appear in the form header.
- **Course codes** — one per line; these become the dropdown when adding a
  session. (Defaults are example COMS codes — replace with yours.)
- **Logo path** — leave blank to use the bundled `assets/wits_logo.png`, or point
  to your own image.

Settings are saved to `data/settings.json` on your machine.

---

## Day-to-day use

**After each tutoring session**

1. Click **+ Add session**.
2. Pick the date, course code, and activity; set start/end times. Hours fill in
   automatically (tick *override* only if needed).
3. **Save**. Edit or delete any row later from the table.

**At the end of the month**

1. Choose **Month of Claim** and **Year**.
2. Click **Generate Form →**. The `.docx` downloads automatically (and is also
   saved in `output/`).
3. Open it, check it, and submit it to your School.

Only the selected month's sessions go into each form, so you can keep recording
straight into the next month.

---

## Changing the fixed boilerplate (block dates, NB bullets)

The submission-dates table and the red bullet list are university-wide text. They
live in `data/settings.json` under `submission_rows` and `bullets`. If the
university updates the block dates or wording (e.g. a new year), edit those values
in `data/settings.json` and save. The defaults are defined in `tff/config.py`.

---

## Project structure

```
server.py             Flask web server — the entry point
templates/index.html  Web UI markup
static/style.css      Dark theme
static/app.js         Frontend logic (add/edit/generate, live hours)
tff/
  config.py           Defaults, paths, boilerplate, logo resolution
  models.py           Session model + hours calculation/formatting
  storage.py          Read/write the JSON data files
  docx_writer.py      Builds the .docx exactly to the form spec
assets/wits_logo.png  Bundled Wits crest (used by default)
data/                 Your sessions.json + settings.json (auto-created, git-ignored)
output/               Generated timesheets (auto-created, git-ignored)
requirements.txt      python-docx, Flask
Run TFF.bat           Double-click launcher (Windows)
```

`data/` and `output/` are git-ignored, so cloning the repo never carries another
tutor's personal details or forms — each person fills in their own under Settings.

---

## Troubleshooting

- **`python` not recognised** — Python isn't on PATH. Reinstall it and tick
  “Add Python to PATH”, or run with the full path.
- **`No module named flask` / `docx`** — run `python -m pip install -r requirements.txt`.
- **Browser didn't open** — go to <http://127.0.0.1:5000> manually.
- **Form has a placeholder instead of the crest** — your logo path points to a
  missing file. Clear the Logo path in Settings (to use the bundled crest) or fix
  the path.
- **“No sessions recorded for …”** — you have no sessions in that month/year; add
  some or change the selector.
