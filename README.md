# DiscoveryTool

DiscoveryTool is a FastAPI + Next.js application for discovery support workflows. It packages two CSV conversion tools behind a lightweight web UI, and the containerized build serves the frontend and API from one process.

## Tools

### `RFP CSV to Pleading`

Use this tool when you have a tagged production CSV and need pleading-ready text for RFP or ROG sections.

Expected input:

- column `A`: begin Bates
- column `B`: end Bates
- column `C` and beyond: `Tag: RFP ...` or `Tag: ROG ...` columns
- responsive rows marked with `TRUE`

What the tool does:

- groups and merges responsive Bates ranges by RFP or ROG label
- shows skipped-row warnings for bad Bates values or malformed ranges
- lets you keep or remove empty sections before download
- downloads a `.txt` file named after the uploaded CSV

Typical usage:

1. Open `/tools/rfp-csv-to-pleading/`.
2. Use `View tutorial` if you need the Logikcull export steps.
3. Upload the CSV and click `Convert CSV`.
4. Review the preview, toggle empty sections if needed, then click `Download TXT`.

### `Privilege Log Preparation`

Use this tool when you have a privilege export and need a clean privilege log CSV for review or paste-in workflows.

Expected input:

- `Begin Bates num from ...`
- `End Bates num from ...`
- `Document Date`
- `File Name`
- `Email Subject`
- `Email From`
- `Email To`
- `Email CC`
- `Email BCC`
- `Tag: Privilege - Redact`
- `Tag: Privilege - Withhold`
- at least one privilege reason column after `Tag: Privilege - Withhold`

What the tool does:

- requires exactly one of redact or withhold to be marked `TRUE` per row
- builds the description from `Email Subject`, falling back to `File Name`
- merges recipient fields into one output column
- rewrites the export into review-ready privilege log rows
- downloads a `.csv` file named `<source>-privilege-log.csv`

Typical usage:

1. Open `/tools/privilege-log/`.
2. Upload the privilege CSV and click `Convert CSV`.
3. Review the table preview and any normalization warnings.
4. Click `Download CSV` when the output looks right.

## Project structure

- `backend/`: FastAPI API, CSV conversion logic, and Python tests
- `frontend/`: Next.js App Router frontend built with Once UI Core
- `frontend/public/`: static assets served directly by the frontend build
- `examples/rfp/`: sample CSV inputs used for development and integration tests
- `examples/privilege/`: sample privilege export inputs and expected-output references
- `RFP_TUTORIAL.md`: source markdown for the in-app RFP export tutorial

## Tutorial assets

The RFP tutorial is authored in [RFP_TUTORIAL.md](RFP_TUTORIAL.md). Its screenshots live in `frontend/public/images/rfp`.

When editing the tutorial:

- reference screenshots with repo-relative paths like `frontend/public/images/rfp/example.png`
- keep the actual screenshot files under `frontend/public/images/rfp`
- do not recreate a duplicate top-level `images/` directory

At render time, the frontend rewrites those markdown paths to public browser URLs such as `/images/rfp/example.png`.

## API routes

- `GET /api/health`: health check
- `POST /api/rfp/convert`: converts a tagged production CSV into TXT output plus preview metadata
- `POST /api/privilege/convert`: converts a privilege export CSV into a review-ready CSV plus preview metadata

## Local development

### Backend

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -r backend\requirements-dev.txt
.\.venv\Scripts\python -m uvicorn app.main:app --app-dir backend --reload
```

Backend URLs:

- `http://localhost:8000/api/health`
- `http://localhost:8000/api/rfp/convert`
- `http://localhost:8000/api/privilege/convert`

### Frontend

```powershell
cd frontend
npm install
npm run dev
```

Frontend URL:

- `http://localhost:3000/`

The frontend defaults to calling `/api`. For local split-port development, set `NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api`.

## Example data

- `examples/rfp/example1.csv`, `example2.csv`, and `example3.csv` cover tagged production exports used by the RFP converter tests.
- `examples/privilege/example.csv` is a sample privilege export used by the privilege log tests.

## Verification

```powershell
.\.venv\Scripts\python -m pytest backend\tests
cd frontend
npm run lint
npm run test
npm run build
```

## Docker

```powershell
docker build --no-cache -t discoverytool .
docker run --rm -p 8000:8000 discoverytool
```

The container serves the compiled frontend and the FastAPI backend together on port `8000`.

Then open:

- `http://localhost:8000/`
- `http://localhost:8000/api/health`

Important:

- `0.0.0.0` is the bind/listen address inside the container, not the browser URL to visit.
- If you need access from another device, use your machine's LAN IP instead of `localhost`.

Or with Compose:

```powershell
docker compose build --no-cache
docker compose up --force-recreate
```

The Compose file also sets `build.no_cache: true` for the `discoverytool` service so `docker compose up --build` does not reuse stale image layers.
