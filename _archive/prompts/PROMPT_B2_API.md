# Fase B2: HTTP API voor PDF generatie (FastAPI)

## Context

De report generator heeft een werkende Python library (`bm_reports`) met `Report.from_dict()` en `Report.build()`. Er is een CLI (`cli.py`), maar geen HTTP API. De React frontend genereert JSON en heeft een endpoint nodig om PDF's te genereren en te downloaden.

Bekijk voor je begint:
- `src/bm_reports/core/engine.py` — `Report.from_dict()` en `Report.from_json()`
- `src/bm_reports/core/template_loader.py` — `TemplateLoader.list_templates()`
- `src/bm_reports/core/brand.py` — `BrandLoader.list_brands()`
- `src/bm_reports/data/json_adapter.py` — `JsonAdapter.validate()`
- `schemas/report.schema.json` — het JSON schema (single source of truth)
- `src/bm_reports/cli.py` — bestaande CLI (niet wijzigen, de API is een apart entrypoint)

## Wat er moet komen

### 1. FastAPI applicatie — `src/bm_reports/api.py`

Eén bestand met alle endpoints. Gebruik FastAPI + uvicorn.

**Dependencies toevoegen aan `pyproject.toml`:**
```
fastapi>=0.115.0
uvicorn[standard]>=0.30.0
python-multipart>=0.0.9
```

### 2. Endpoints

#### `POST /api/generate` — Genereer PDF uit JSON

Accepteert JSON body conform `report.schema.json`. Retourneert PDF als binary response.

```python
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from tempfile import NamedTemporaryFile
from pathlib import Path

@app.post("/api/generate")
async def generate_report(data: dict):
    """Genereer PDF rapport uit JSON data.
    
    Body: JSON conform report.schema.json
    Response: application/pdf binary
    """
    try:
        report = Report.from_dict(data, brand=data.get("brand", "3bm_cooperatie"))
        
        with NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            output_path = Path(tmp.name)
        
        report.build(output_path)
        
        return FileResponse(
            path=str(output_path),
            media_type="application/pdf",
            filename=f"{data.get('project', 'rapport')}.pdf",
            background=BackgroundTask(lambda: output_path.unlink(missing_ok=True)),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

**Belangrijk:**
- Gebruik `BackgroundTask` om temp files op te ruimen NA verzending
- Filename in Content-Disposition header: `{project}_{project_number}.pdf` (sanitize special chars)
- Timeout: stel een redelijke max in (bijv. 60 sec) — kaarten ophalen kan langzaam zijn
- Max request size: limiteer tot 50MB (base64 images in JSON kunnen groot zijn)

#### `POST /api/generate` met base64 images

De frontend stuurt images als base64 in de JSON. Dit werkt al via `resolve_image_source()` in `block_registry.py`. Geen extra werk nodig — de `Report.from_dict()` pipeline handelt dit af.

#### `POST /api/validate` — Valideer JSON tegen schema

```python
import jsonschema

SCHEMA_PATH = Path(__file__).parent.parent.parent / "schemas" / "report.schema.json"

@app.post("/api/validate")
async def validate_report(data: dict):
    """Valideer JSON data tegen report.schema.json.
    
    Returns: {"valid": true} of {"valid": false, "errors": [...]}
    """
    schema = json.loads(SCHEMA_PATH.read_text())
    validator = jsonschema.Draft7Validator(schema)
    errors = [
        {"path": "/".join(str(p) for p in e.absolute_path), "message": e.message}
        for e in validator.iter_errors(data)
    ]
    return {"valid": len(errors) == 0, "errors": errors}
```

**Dependency:** `jsonschema>=4.20.0` — toevoegen aan pyproject.toml.

#### `GET /api/templates` — Lijst beschikbare templates

```python
@app.get("/api/templates")
async def list_templates():
    loader = TemplateLoader()
    return {"templates": loader.list_templates()}
```

#### `GET /api/templates/{name}/scaffold` — Template scaffold (zie Fase B3)

Placeholder endpoint — wordt in Fase B3 ingevuld:

```python
@app.get("/api/templates/{name}/scaffold")
async def get_template_scaffold(name: str):
    # Fase B3 implementatie
    raise HTTPException(status_code=501, detail="Scaffold nog niet geïmplementeerd")
```

#### `GET /api/brands` — Lijst beschikbare brands

```python
@app.get("/api/brands")
async def list_brands():
    loader = BrandLoader()
    return {"brands": loader.list_brands()}
```

#### `GET /api/health` — Health check

```python
@app.get("/api/health")
async def health():
    return {"status": "ok", "version": __version__}
```

### 3. CORS configuratie

De frontend draait op `localhost:5173` (Vite default). CORS moet open voor development:

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 4. Error handling

Gebruik een globale exception handler voor nette error responses:

```python
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.exception("Onverwachte fout bij %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content={"detail": "Interne serverfout", "type": type(exc).__name__},
    )
```

Specifieke exceptions:
- `FileNotFoundError` (ontbrekende template/brand) → 404
- `ValueError` (ongeldige data) → 422
- `jsonschema.ValidationError` → 422 met details
- `requests.Timeout` (PDOK timeout bij map) → 504

### 5. Server entrypoint

Voeg een `__main__` block toe aan `api.py`:

```python
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("bm_reports.api:app", host="0.0.0.0", port=8000, reload=True)
```

En voeg een CLI commando toe aan `cli.py`:

```python
# In het subparser blok:
serve_parser = subparsers.add_parser("serve", help="Start API server")
serve_parser.add_argument("--host", default="0.0.0.0")
serve_parser.add_argument("--port", "-p", type=int, default=8000)
serve_parser.add_argument("--reload", action="store_true", default=False)

# In het command dispatch:
elif args.command == "serve":
    _cmd_serve(args)

def _cmd_serve(args):
    import uvicorn
    print(f"3BM Report API server op http://{args.host}:{args.port}")
    print("  Docs: http://localhost:{args.port}/docs")
    uvicorn.run("bm_reports.api:app", host=args.host, port=args.port, reload=args.reload)
```

### 6. Filename sanitization

Helper functie voor veilige bestandsnamen:

```python
import re

def _safe_filename(*parts: str, extension: str = ".pdf") -> str:
    """Maak een veilige bestandsnaam van project info."""
    combined = "_".join(p for p in parts if p)
    safe = re.sub(r'[^\w\s-]', '', combined).strip()
    safe = re.sub(r'[-\s]+', '_', safe)
    return (safe or "rapport") + extension
```

Gebruik: `filename=_safe_filename(data.get("project_number"), data.get("project"))`

## File structuur na implementatie

```
src/bm_reports/
├── api.py              # NIEUW — FastAPI app
├── cli.py              # AANGEPAST — serve commando toegevoegd
├── __init__.py
├── core/
├── components/
├── data/
├── ...
```

## Tests

Maak `tests/test_api.py`:

```python
from fastapi.testclient import TestClient
from bm_reports.api import app

client = TestClient(app)

def test_health():
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"

def test_list_templates():
    r = client.get("/api/templates")
    assert r.status_code == 200
    assert "templates" in r.json()

def test_list_brands():
    r = client.get("/api/brands")
    assert r.status_code == 200
    assert "brands" in r.json()

def test_generate_minimal():
    data = {
        "template": "structural",
        "project": "API Test",
        "project_number": "T-001",
        "sections": [{"title": "Test", "content": [{"type": "paragraph", "text": "Hallo."}]}]
    }
    r = client.post("/api/generate", json=data)
    assert r.status_code == 200
    assert r.headers["content-type"] == "application/pdf"
    assert len(r.content) > 500

def test_generate_with_cover():
    data = {
        "template": "structural",
        "project": "Cover API Test",
        "project_number": "T-002",
        "cover": {"subtitle": "Test ondertitel"},
        "colofon": {"enabled": True},
        "sections": [{"title": "Inhoud", "content": []}],
        "backcover": {"enabled": True}
    }
    r = client.post("/api/generate", json=data)
    assert r.status_code == 200
    assert r.headers["content-type"] == "application/pdf"

def test_validate_valid():
    data = {"template": "structural", "project": "Test", "sections": []}
    r = client.post("/api/validate", json=data)
    assert r.status_code == 200
    assert r.json()["valid"] is True

def test_validate_invalid():
    data = {"sections": []}  # missing required 'project' and 'template'
    r = client.post("/api/validate", json=data)
    assert r.status_code == 200
    assert r.json()["valid"] is False
    assert len(r.json()["errors"]) > 0

def test_generate_invalid_returns_error():
    r = client.post("/api/generate", json={})
    assert r.status_code in (422, 500)
```

**Test dependency:** `httpx` (vereist door FastAPI TestClient) — toevoegen aan dev dependencies.

## Verificatie

```bash
pip install fastapi uvicorn jsonschema httpx
python -m pytest tests/test_api.py -v
python -m pytest tests/ -v  # regressie

# Handmatige test:
python -m bm_reports.api
# Open http://localhost:8000/docs → Swagger UI
# Test /api/generate met een JSON body
```
