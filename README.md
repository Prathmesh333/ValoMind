# ValoMind

[Open the video-processing notebook in Colab](https://colab.research.google.com/github/Prathmesh333/ValoMind/blob/main/notebooks/VCT_video_jobs.ipynb)

The notebook accepts YouTube links and runs sampled broadcast filtering, OCR,
roster proposals and optional model training in the cloud. Select a T4 GPU and
start with the two-minute preview. See [notebook instructions](notebooks/README.md).
Agent classification requires a separately trained model; generated observations
remain proposals. Downloaded footage, result exports and weights stay out of Git.

Offline VALORANT coaching research. The original implementation contract is in
[ValoMind_Codex_Docs](ValoMind_Codex_Docs/README.md).

M0 is in progress. This increment provides the Python API foundation, an immutable
Alembic schema snapshot, PostgreSQL/Redis Compose configuration, synthetic fixture
access, tests and a Python lockfile. Frontend, workspace authentication, upload,
annotation and training are still pending. No real footage has been processed.

## Run locally (PowerShell)

Install Python 3.13 and uv. From this directory:

```powershell
uv sync --locked
Copy-Item .env.example .env
$env:DEMO_ACCESS_TOKEN = uv run python -c "import secrets; print(secrets.token_urlsafe(32))"
uv run uvicorn valomind.main:app --app-dir apps/api --host 127.0.0.1 --port 8000
```

Open http://127.0.0.1:8000/docs for API documentation. In another terminal, set
the same token and request the fixture using a bearer header:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/api/v1/demo/match -Headers @{Authorization="Bearer $env:DEMO_ACCESS_TOKEN"}
```

The fixture route is disabled when the token is empty or DEMO_SYNTHETIC=false.
This token protects synthetic fixtures only; it is not workspace authentication.
Liveness works without PostgreSQL. Readiness returns 503 until the database is
reachable and migrated.

## Database (requires Docker Compose)

Set a local development password and a matching DATABASE_URL in `.env` or your
shell. Use a URL-safe password, or URL-encode it in the database URL.

```powershell
$env:POSTGRES_PASSWORD = 'choose-a-local-development-password'
$env:DATABASE_URL = "postgresql+psycopg://valomind:$($env:POSTGRES_PASSWORD)@localhost:5432/valomind"
docker compose -f infra/compose.yaml up -d
uv run alembic upgrade head
```

`uv run alembic downgrade base` removes all application tables and their data.
Use it only on a disposable development database. `docker compose -f
infra/compose.yaml down` stops services and retains the database volume.
The migration creates tables; fixture access reads JSON and does not seed them.

## Check

```powershell
uv run ruff check .
uv run ruff format --check .
uv run pytest -q
uv run alembic upgrade head --sql
```

CI also applies, reverses and reapplies the migration against PostgreSQL. The
[first successful CI run](https://github.com/Prathmesh333/ValoMind/actions/runs/39404925597)
passed lint, formatting, all 64 tests and all three migration steps. Docker remains
unavailable on the local implementation machine.
See [the training plan](docs/VIDEO_MODEL_PLAN.md) and [current progress](docs/PROGRESS.md).
