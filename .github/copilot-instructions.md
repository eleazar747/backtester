## Purpose
Provide concise, repository-specific guidance so AI coding agents can be immediately productive in this Django codebase.

## Big picture (what to know first)
- **Type:** Django project (multiple apps) with Channels (ASGI) and several standalone "processor" scripts that populate models from external data sources.
- **Apps:** key Django apps: `historical_price`, `referential`, `strategy`, `macroeconomie`, `realtime_price`, `scheduler`. See [stockmarket/settings.py](stockmarket/settings.py#L1-L80).
- **Data flow:** referential -> historical processors -> models. Example: `referential.models.securitydescription` is consumed by `historical_price/processor/historical_price.py` which uses `yfinance` and writes `historical_price` records.
- **Persistence:** SQLite file `db.sqlite3` with per-app migrations present in each `migrations/` folder.

## How to run & common dev workflows
- Activate virtualenv (Windows): `env\Scripts\activate` (env is in repo top-level).
- Install dependencies: `pip install -r requirements.txt` ([requirements.txt](requirements.txt)).
- Run migrations: `python manage.py migrate` ([manage.py](manage.py)).
- Run server (development): `python manage.py runserver` — project uses Channels/ASGI (`ASGI_APPLICATION` in [stockmarket/settings.py](stockmarket/settings.py#L40-L60)). For ASGI/Daphne usage prefer `daphne stockmarket.asgi:application` if needed.
- Run tests: `python manage.py test`.
- Database: local development uses `db.sqlite3` (no external DB config by default).

## Project-specific conventions & patterns
- Processors live inside each app under `*/processor/` (examples: [historical_price/processor/historical_price.py](historical_price/processor/historical_price.py#L1-L40), [referential/processor/loadReferential.py](referential/processor/loadReferential.py#L1-L80)). They are not Django management commands — they are plain modules with entry functions (e.g. `start_load_histo_data`) intended to be invoked by the scheduler, a custom script, or the interactive shell.
- Bulk writes: processors typically use `bulk_create` for performance when persisting time-series data; follow existing field mappings instead of inventing new schemas.
- Threading: some processors start multiple `threading.Thread` workers (see `historical_price/processor/historical_price.py`) — preserve thread-safety and DB transaction semantics when editing.
- Models/Serializers: apps follow Django conventions — models, serializers, views split across app folders. Look at `historical_price/models.py` and `historical_price/serializers.py` for examples of model fields and serializer patterns.

## Integration points & external dependencies
- External data via `yfinance` (used in `historical_price`), `eikon` and other market-data libs (listed in `requirements.txt`).
- REST API uses Django REST Framework (`rest_framework` in INSTALLED_APPS).
- Channels is installed (`channels` in INSTALLED_APPS) and `ASGI_APPLICATION` is set — websocket/async features may require running an ASGI server in production.
- Frontend assets: static Angular-like assets are under `static/ang/` and templates under `templates/` (useful for UI edits).

## Files and places to inspect for common tasks (examples)
- Start point: [manage.py](manage.py)
- Settings: [stockmarket/settings.py](stockmarket/settings.py#L1-L200)
- Historical data loader: [historical_price/processor/historical_price.py](historical_price/processor/historical_price.py#L1-L200)
- Referential loader: [referential/processor/loadReferential.py](referential/processor/loadReferential.py#L1-L200)
- Requirements: [requirements.txt](requirements.txt)

## When editing or adding code
- Follow existing app structure: add signal handlers, processors, or management commands under the same app when the change is app-scoped.
- For heavy data imports prefer `bulk_create` and chunking (see `historical_price/processor/historical_price.py`).
- Preserve existing DB schema and migration flow: add model changes via `makemigrations` and commit migration files under the app's `migrations/` folder.

## Safety notes for AI agents
- Do not assume an external DB or credentials — this repo uses local SQLite by default.
- Avoid long-running blocking operations in request handlers; processors are externalized to `processor/` modules intentionally.
- When changing code that touches processors, run a small subset locally (or dry-run) because processors can insert large amounts of data into the DB.

## Quick checklist for PRs
- Run `python manage.py test` and `python manage.py migrate` locally.
- If adding model fields, create and commit migrations under the correct app.
- Document new processor entry points and update README or this file.

If anything here is unclear or you want more coverage of specific areas (ASGI run, scheduler integration, or where the UI lives), tell me which part and I'll expand or adjust these instructions.
