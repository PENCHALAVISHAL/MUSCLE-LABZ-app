## FITNESS TRACKER — Flask Web App

Modern, full‑featured fitness tracking app built with Flask. It lets users register/login, enter basic profile data, log workouts, track hydration and weight, estimate target dates with linear regression, calculate and log body‑fat percentage, and view rich analytics and suggestions.

### Key Features
- **Authentication**: Email/password with secure hashing; login required for app sections.
- **User Profile**: Collects name, age, height, weight, body fat (optional), gender, activity level, and fitness goal.
- **Dashboard**: Quick entry point after onboarding.
- **Workout Tracker**: Log exercise, weight (kg/lbs), reps, sets, notes; browse exercise categories populated from an exercise library; view and bulk‑delete logs.
- **Analytics**:
  - Daily training volume by exercise (stacked view)
  - Most frequent exercises
  - Average reps per exercise
  - Workout category distribution (pie)
- **Hydration Tracking**: Daily water logs with a dynamic goal — uses user’s latest weight (×35 ml) or a default of 2000 ml; supports custom per‑user goal via `HydrationGoal` table.
- **Weight Tracking**: Daily weight logs, charting, and a linear regression trendline; goal weight and estimated date to reach it.
- **Body Fat Calculator & Tracker**: US Navy method (waist/neck[/hip]) with gender support; logging, goal body‑fat %, trendline and estimated goal‑date.
- **Suggestions**: Personalized tips derived from your own logs plus curated training/hydration/weight/body‑fat guidance.

### Tech Stack
- **Backend**: Flask 3, Flask‑Login, Flask‑SQLAlchemy
- **Database**: SQLite (local `instance/fitness_tracker.db`) or PostgreSQL in production
- **ML/Analysis**: NumPy, scikit‑learn (LinearRegression)
- **Frontend**: Jinja2 templates, static assets (CSS/JS/images)
- **Deployment**: Gunicorn (Procfile), Render (`render.yaml`)

---

## Project Structure

```
FITNESS TRACKER/
  app.py                # Flask app factory, routes, CLI commands
  config.py             # Config classes and DB URI wiring
  models.py             # SQLAlchemy models
  wsgi.py               # WSGI entrypoint (creates app)
  instance/
    fitness_tracker.db  # SQLite database (created at runtime)
  templates/            # Jinja2 templates (pages)
  static/               # CSS/JS/images/fonts
  requirements.txt      # Python dependencies
  Procfile              # Gunicorn start command for prod
  render.yaml           # Render.com service definition
```

Note: `db.py` exists but is a legacy/unused module that performs raw SQLite operations without hashing. The live app uses `models.py` + Flask‑SQLAlchemy with hashed passwords. Do not use `db.py` in production.

---

## Data Model Overview

- `User`: id, username, email, password_hash, created_at
  - Relationships: one `UserData`, many `Workout`, many `WeightTracking`, many `BodyFatTracking`, many `HydrationTracking`, one `HydrationGoal`
- `UserData`: profile and targets (name, age, height, weight, gender, activity_level, fitness_goal, goal_weight, goal_body_fat)
- `ExerciseLibrary`: seedable exercise catalog (name, category, muscle_group, description)
- `Workout`: per‑session logs (date, exercise, weight kg, reps, sets, notes)
- `HydrationTracking`: water intake logs (amount ml, date, notes)
- `HydrationGoal`: per‑user daily ml goal
- `WeightTracking`: daily weight logs (kg)
- `BodyFatTracking`: calculated body‑fat %, neck/waist/hip, goal history

---

## Routes (User‑Facing)

- `GET /` → redirect to `/welcome`
- `GET /welcome` → landing page
- `GET|POST /register` → create account
- `GET|POST /login` → sign in
- `GET /logout` → sign out
- `GET|POST /basic_info` → enter/update profile
- `GET /dashboard` → main dashboard
- `GET /workout_tracker` → workout log form (exercise categories)
- `GET /workouts/view` → list workouts + charts; bulk delete via POST `/delete_workouts`
- `GET /analytics` → advanced charts (volume, frequency, reps, distribution)
- `GET /hydration` → hydration widget for today
- `GET /hydration/view` → hydration history; bulk delete via POST `/delete_hydration_entries`
- `POST /log_hydration` → JSON body `{ amount }` to add today’s ml
- `GET|POST /weight` → view/add today’s weight, set goal, see trend and ETA
- `GET /weight/view` → weight history; bulk delete via POST `/delete_weight_entries`
- `GET|POST /bodyfat` → calculate/log body fat; set goal, trend and ETA
- `GET /bodyfat/view` → body‑fat logs, goal history; bulk delete via POST `/delete_bodyfat_entries`
- `GET /suggestions` → personalized guidance

### API/AJAX Helpers
- `GET /api/exercises?category=Chest` → returns `[{ name: string }]`
- `POST /log_hydration` → JSON `{ amount: number }` → `{ today_total, hydration_goal }`

---

## CLI Utilities (Flask commands)

Run with: `flask --app app.py <command>`

- `init-db` → create all tables
- `reset-db` → drop and recreate all tables
- `populate-exercises` → seed `exercise_library` with common movements

Example:
```bash
flask --app app.py init-db
flask --app app.py populate-exercises
```

---

## Getting Started (Local)

Prereqs: Python 3.13+ recommended on Windows (PowerShell), Git.

1) Clone and enter the project folder.
```powershell
git clone <your-fork-or-repo-url>
cd "FITNESS TRACKER"
```

2) Create and activate a virtual environment.
```powershell
python -m venv venv
venv\Scripts\Activate.ps1
```

3) Install dependencies.
```powershell
pip install -r requirements.txt
```

4) Configure environment variables (optional but recommended).
- `SECRET_KEY` — Flask session secret.
- `DATABASE_URL` — set to a PostgreSQL URL in production; locally you can omit to use SQLite at `instance/fitness_tracker.db`.

You can place these in a `.env` file (auto‑loaded via `python-dotenv`):
```
SECRET_KEY=change_me
DATABASE_URL=sqlite:///instance/fitness_tracker.db
```

5) Initialize the database and seed exercises.
```powershell
flask --app app.py init-db
flask --app app.py populate-exercises
```

6) Run the server (development).
```powershell
python app.py
# App starts on http://127.0.0.1:8080
```

Login flow: register → login → complete `Basic Info` → `Dashboard`.

---

## Deployment

### Procfile (Gunicorn)
```
web: gunicorn app:app
```

### Render.com
`render.yaml` includes a web service definition. Ensure it points to your repo and set environment variables in the Render dashboard:
- `SECRET_KEY`
- `DATABASE_URL` (e.g., `postgres://...`)

The service start command is already `gunicorn app:app`.

---

## Security & Notes
- Passwords are securely hashed via Werkzeug (`User.set_password`).
- Ensure `SECRET_KEY` is set in production.
- SQLite file lives under `instance/`. Render/containers should use Postgres instead.
- The `db.py` module is legacy and not used by the app’s Flask routes; avoid using it.

---

## Troubleshooting
- If the `instance/` folder doesn’t exist, the app will create it at startup.
- If charts show no data, seed exercises (`populate-exercises`) and add logs.
- For LinearRegression trend/ETA, you’ll need 2+ data points and an active goal.
- On Windows, if `Activate.ps1` is blocked, enable scripts: `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` in an elevated PowerShell.





