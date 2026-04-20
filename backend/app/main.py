from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from app.models import ConversionResponse, PrivilegeConversionResponse
from app.services.privilege_converter import (
    ConversionError as PrivilegeConversionError,
    convert_csv_bytes as convert_privilege_csv_bytes,
)
from app.services.rfp_converter import ConversionError, convert_csv_bytes

BASE_DIR = Path(__file__).resolve().parents[2]
FRONTEND_DIST_DIR = Path(os.getenv("FRONTEND_DIST_DIR", BASE_DIR / "frontend" / "out"))

app = FastAPI(title="Discovery Tool API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def healthcheck() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/rfp/convert", response_model=ConversionResponse)
async def convert_rfp_csv(file: UploadFile = File(...)) -> ConversionResponse:
    filename = file.filename or "uploaded.csv"
    payload = await file.read()

    if not payload:
        raise HTTPException(status_code=400, detail="The uploaded CSV is empty.")

    try:
        return convert_csv_bytes(filename=filename, raw_bytes=payload)
    except ConversionError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/privilege/convert", response_model=PrivilegeConversionResponse)
async def convert_privilege_csv(file: UploadFile = File(...)) -> PrivilegeConversionResponse:
    filename = file.filename or "uploaded.csv"
    payload = await file.read()

    if not payload:
        raise HTTPException(status_code=400, detail="The uploaded CSV is empty.")

    try:
        return convert_privilege_csv_bytes(filename=filename, raw_bytes=payload)
    except PrivilegeConversionError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/{full_path:path}", include_in_schema=False)
def serve_frontend(full_path: str) -> FileResponse:
    if not FRONTEND_DIST_DIR.exists():
        raise HTTPException(status_code=404, detail="Frontend assets are not available.")

    requested_path = (FRONTEND_DIST_DIR / full_path).resolve()
    if requested_path.is_file() and requested_path.is_relative_to(FRONTEND_DIST_DIR):
        return FileResponse(requested_path)

    candidates = []
    if full_path:
        candidates.extend(
            [
                FRONTEND_DIST_DIR / full_path / "index.html",
                FRONTEND_DIST_DIR / f"{full_path}.html",
            ]
        )

    candidates.append(FRONTEND_DIST_DIR / "index.html")

    for candidate in candidates:
        resolved = candidate.resolve()
        if resolved.is_file() and resolved.is_relative_to(FRONTEND_DIST_DIR):
            return FileResponse(resolved)

    not_found_page = FRONTEND_DIST_DIR / "404.html"
    if not_found_page.exists():
        return FileResponse(not_found_page, status_code=404)

    raise HTTPException(status_code=404, detail="Page not found.")
