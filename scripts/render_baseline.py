"""Render deterministische baseline-PDF's + PNG's voor pixel-regressietests.

Doel: vóór de renderer_v2 refactor (CoverGenerator/ColofonGenerator worden
data-gedreven) een baseline vastleggen van de huidige pixel-output, per
tenant. ``diff_baseline.py`` vergelijkt latere renders tegen deze baseline.

Belangrijke constatering (zie rapportage aan gebruiker): renderer_v2's
``TemplateSet`` laadt altijd exact dezelfde 6 vaste bestandsnamen
(``cover.yaml``, ``colofon.yaml``, ``toc.yaml``, ``standaard.yaml``,
``content_styles.yaml``, ``bijlage.yaml``) — het JSON-veld ``data["template"]``
wordt door ``ReportGeneratorV2`` nergens gelezen. De package-brede
``list_templates()`` catalogus (structural/building_code/daylight/custom)
hoort bij een ANDER renderpad (``Report.from_dict`` / ``TemplateEngine``),
niet bij ``ReportGeneratorV2``. Er bestaat dus, voor deze renderer, precies
één template-configuratie per tenant. ``TEMPLATES_BY_TENANT`` bevat daarom
één logische naam per tenant ("standaard") — de loop-structuur blijft intact
zodat een toekomstige multi-template-situatie zonder herstructurering kan
worden toegevoegd.

Usage:
    .venv/Scripts/python.exe scripts/render_baseline.py
"""

from __future__ import annotations

import hashlib
import json
import sys
import traceback
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = REPO_ROOT / "src"
TENANTS_DIR = REPO_ROOT / "tenants"
FIXTURE_PATH = REPO_ROOT / "tests" / "fixtures" / "baseline_report.json"
BASELINE_DIR = REPO_ROOT / "tests" / "baseline"
FAILURES_PATH = BASELINE_DIR / "FAILURES.md"
MANIFEST_PATH = BASELINE_DIR / "manifest.json"

RASTER_DPI = 100

# tenant_slug -> lijst van logische template-namen (zie module-docstring
# voor waarom dit er per tenant maar 1 is bij ReportGeneratorV2).
TEMPLATES_BY_TENANT: dict[str, list[str]] = {
    "3bm": ["standaard"],
    "openaec_foundation": ["standaard"],
}

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

import os  # noqa: E402

os.environ["OPENAEC_TENANTS_ROOT"] = str(TENANTS_DIR)
os.environ["OPENAEC_TENANTS_DIR"] = str(TENANTS_DIR)

import fitz  # noqa: E402

from openaec_reports.core.renderer_v2 import ReportGeneratorV2  # noqa: E402


def _load_fixture() -> dict:
    with open(FIXTURE_PATH, encoding="utf-8") as f:
        return json.load(f)


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _rasterize(pdf_path: Path, out_dir: Path) -> list[tuple[str, str]]:
    """Rasterize elke pagina van ``pdf_path`` naar PNG in ``out_dir``.

    Returns:
        Lijst van (bestandsnaam, sha256) tuples, in paginavolgorde.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    entries: list[tuple[str, str]] = []
    doc = fitz.open(str(pdf_path))
    try:
        for i, page in enumerate(doc, start=1):
            pix = page.get_pixmap(dpi=RASTER_DPI)
            png_bytes = pix.tobytes("png")
            filename = f"page_{i:03d}.png"
            (out_dir / filename).write_bytes(png_bytes)
            entries.append((filename, _sha256(png_bytes)))
    finally:
        doc.close()
    return entries


def _log_failure(tenant: str, template: str, exc: BaseException) -> None:
    BASELINE_DIR.mkdir(parents=True, exist_ok=True)
    header_exists = FAILURES_PATH.exists()
    with open(FAILURES_PATH, "a", encoding="utf-8") as f:
        if not header_exists:
            f.write("# Baseline render failures\n\n")
            f.write(
                "Elke sectie hieronder is een render die is mislukt tijdens "
                "`render_baseline.py`. Dit bestand wordt bij elke run "
                "aangevuld (niet overschreven) zodat historie behouden blijft.\n\n"
            )
        f.write(f"## {tenant} / {template} — {datetime.now(timezone.utc).isoformat()}\n\n")
        f.write("```\n")
        f.write("".join(traceback.format_exception(type(exc), exc, exc.__traceback__)))
        f.write("```\n\n")


def main() -> int:
    fixture = _load_fixture()

    manifest: dict = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "raster_dpi": RASTER_DPI,
        "fixture": str(FIXTURE_PATH.relative_to(REPO_ROOT)),
        "reports": [],
    }

    successes: list[str] = []
    failures: list[str] = []

    for tenant, templates in TEMPLATES_BY_TENANT.items():
        tenant_dir = TENANTS_DIR / tenant
        if not tenant_dir.exists():
            print(f"[SKIP] tenant '{tenant}' niet gevonden op {tenant_dir}")
            continue
        stationery_dir = tenant_dir / "stationery"

        for template in templates:
            label = f"{tenant}/{template}"
            print(f"[RENDER] {label} ...")
            out_dir = BASELINE_DIR / tenant / template
            # PDF is een tussenresultaat — alleen de PNG-rasters + hashes
            # zijn het regressie-bewijs, dus de PDF wordt na rasterizen
            # weer verwijderd (scheelt ~4 MB per render in de repo).
            tmp_pdf_dir = BASELINE_DIR / "_render_tmp"
            tmp_pdf = tmp_pdf_dir / f"{tenant}_{template}.pdf"
            try:
                gen = ReportGeneratorV2(brand=tenant, tenant_slug=tenant)
                out_dir.mkdir(parents=True, exist_ok=True)
                tmp_pdf_dir.mkdir(parents=True, exist_ok=True)
                gen.generate(dict(fixture), stationery_dir, tmp_pdf)

                page_entries = _rasterize(tmp_pdf, out_dir)

                manifest["reports"].append(
                    {
                        "tenant": tenant,
                        "template": template,
                        "page_count": len(page_entries),
                        "pages": [
                            {"file": name, "sha256": digest}
                            for name, digest in page_entries
                        ],
                    }
                )
                successes.append(label)
                print(f"[OK] {label} — {len(page_entries)} pagina's")
            except Exception as exc:  # noqa: BLE001 — bewust breed: elke failure loggen, doorgaan
                _log_failure(tenant, template, exc)
                failures.append(label)
                print(f"[FAIL] {label} — {exc!r} (zie {FAILURES_PATH.relative_to(REPO_ROOT)})")
            finally:
                tmp_pdf.unlink(missing_ok=True)

    tmp_pdf_dir = BASELINE_DIR / "_render_tmp"
    if tmp_pdf_dir.exists() and not any(tmp_pdf_dir.iterdir()):
        tmp_pdf_dir.rmdir()

    BASELINE_DIR.mkdir(parents=True, exist_ok=True)
    with open(MANIFEST_PATH, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
        f.write("\n")

    print()
    print(f"Klaar. Succesvol: {len(successes)}, mislukt: {len(failures)}")
    if successes:
        print("  OK:  " + ", ".join(successes))
    if failures:
        print("  FAIL:" + ", ".join(failures))
    print(f"Manifest: {MANIFEST_PATH.relative_to(REPO_ROOT)}")

    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
