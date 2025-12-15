# Help Sell Possible Now - Calendar Events App

Web app to store Calendar Events in **Heroku Postgres**. The `calendar_events` table is designed as a superset of Google Calendar + Microsoft 365 event fields (typed columns for common fields + JSONB for provider-specific/extended fields).

## Tech

- Python 3.12
- Flask (web + API)
- SQLAlchemy (ORM)
- Alembic (migrations)
- Postgres (Heroku)

## Local setup

Create a virtualenv and install deps:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Set environment variables:

```bash
export FLASK_ENV=development
export SECRET_KEY="dev-only"
export DATABASE_URL="postgresql+psycopg://USER:PASSWORD@HOST:5432/DBNAME"
```

Run migrations and start the server:

```bash
alembic upgrade head
gunicorn -b 0.0.0.0:5000 "app:create_app()"
```

Then open `http://localhost:5000`.

You can also copy `EXAMPLE_ENV_VARS.txt` into your own env manager; do not commit secrets.

## Deploy to Heroku

This repo is set up for Heroku with `Procfile` and `release` phase migration.

### Required config vars

- `DATABASE_URL` (Heroku sets this automatically when Heroku Postgres is attached)
- `SECRET_KEY`

### Typical workflow

```bash
# login (interactive) or use a token
heroku login

# if the app already exists:
heroku git:remote -a help-sell-possiblenow

# set SECRET_KEY
heroku config:set SECRET_KEY="replace-me" -a help-sell-possiblenow

# deploy
git add .
git commit -m "Initial calendar events app"
git push heroku main
```

## API quickstart

- `GET /api/events` list
- `POST /api/events` create
- `GET /api/events/<id>` fetch
- `PATCH /api/events/<id>` update
- `DELETE /api/events/<id>` delete

## Public ICS feed

- `GET /calendar.ics` returns an unauthenticated iCalendar (.ics) feed of events (`text/calendar`)
- Optional: `GET /calendar.ics?limit=5000`


