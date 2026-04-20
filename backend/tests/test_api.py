from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_healthcheck() -> None:
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_convert_endpoint_returns_structured_response() -> None:
    csv_bytes = b"Begin,End,Tag: RFP 01\nEXAMPLE_000001,EXAMPLE_000002,TRUE\n"

    response = client.post(
        "/api/rfp/convert",
        files={"file": ("test.csv", csv_bytes, "text/csv")},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["downloadFilename"] == "test.txt"
    assert payload["documentTextWithEmpty"] == "RFP 01:\nEXAMPLE_000001-0002"
    assert payload["stats"] == {
        "total_rows": 1,
        "skipped_rows": 0,
        "total_sections": 1,
        "responsive_sections": 1,
    }


def test_convert_endpoint_uses_example_fixture() -> None:
    example_path = Path(__file__).resolve().parents[2] / "examples" / "rfp" / "example3.csv"

    response = client.post(
        "/api/rfp/convert",
        files={"file": (example_path.name, example_path.read_bytes(), "text/csv")},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["sourceFilename"] == "example3.csv"
    assert payload["stats"]["total_sections"] == 33
    assert payload["sections"][1]["text"] == "RFP 02:\nNo responsive documents."


def test_convert_endpoint_rejects_empty_file() -> None:
    response = client.post(
        "/api/rfp/convert",
        files={"file": ("empty.csv", b"", "text/csv")},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "The uploaded CSV is empty."


def test_convert_privilege_endpoint_returns_structured_response() -> None:
    csv_bytes = (
        b"Begin Bates num from 2026-03-20 Production,End Bates num from 2026-03-20 Production,"
        b"Document Date,File Name,Email Subject,Email From,Email To,Email CC,Email BCC,"
        b"Tag: Privilege - Redact,Tag: Privilege - Withhold,Tag: AC-WP\n"
        b"EXAMPLE003824,EXAMPLE003825,1/24/2025,alpha.msg,Alpha Subject,Author One,To One,,,TRUE,,TRUE\n"
    )

    response = client.post(
        "/api/privilege/convert",
        files={"file": ("priv.csv", csv_bytes, "text/csv")},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["downloadFilename"] == "priv-privilege-log.csv"
    assert payload["rows"] == [
        [
            "EXAMPLE_003824",
            "EXAMPLE_003825",
            "1/24/2025",
            "Alpha Subject",
            "Author One",
            "To One",
            "Redacted - Attorney Client Privilege",
        ]
    ]
    assert payload["stats"] == {
        "total_rows": 1,
        "exported_rows": 1,
        "reason_columns": 1,
    }


def test_convert_privilege_endpoint_rejects_invalid_row_state() -> None:
    csv_bytes = (
        b"Begin Bates num from 2026-03-20 Production,End Bates num from 2026-03-20 Production,"
        b"Document Date,File Name,Email Subject,Email From,Email To,Email CC,Email BCC,"
        b"Tag: Privilege - Redact,Tag: Privilege - Withhold,Tag: AC-WP\n"
        b"EXAMPLE003824,EXAMPLE003825,1/24/2025,alpha.msg,Alpha Subject,Author One,To One,,,,,TRUE\n"
    )

    response = client.post(
        "/api/privilege/convert",
        files={"file": ("priv.csv", csv_bytes, "text/csv")},
    )

    assert response.status_code == 400
    assert "must have exactly one" in response.json()["detail"]


def test_convert_privilege_endpoint_rejects_missing_reason_with_row_bates_context() -> None:
    csv_bytes = (
        b"Begin Bates num from 2026-03-20 Production,End Bates num from 2026-03-20 Production,"
        b"Document Date,File Name,Email Subject,Email From,Email To,Email CC,Email BCC,"
        b"Tag: Privilege - Redact,Tag: Privilege - Withhold,Tag: AC-WP\n"
        b"EXAMPLE003847,EXAMPLE003847,1/15/2025,alpha.msg,Alpha Subject,Author One,To One,,,TRUE,,\n"
    )

    response = client.post(
        "/api/privilege/convert",
        files={"file": ("priv.csv", csv_bytes, "text/csv")},
    )

    assert response.status_code == 400
    assert (
        response.json()["detail"]
        == "Row 2 [EXAMPLE003847]-[EXAMPLE003847] must include at least one privilege reason marked TRUE."
    )
