"""Vergelijk een verse render tegen de vastgelegde baseline (pixel-diff).

Rendert de fixture opnieuw voor elke (tenant, template) uit
``render_baseline.py``, rastert naar PNG, en vergelijkt pixel-voor-pixel met
``tests/baseline/{tenant}/{template}/page_NNN.png``. Bij verschil wordt een
rood-gemarkeerde ``_diff.png`` weggeschreven naast de baseline-pagina.

Exit code 0  → alles identiek (binnen tolerance).
Exit code 1  → verschil gevonden, of baseline ontbreekt.

Usage:
    .venv/Scripts/python.exe scripts/diff_baseline.py [--tolerance N]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = REPO_ROOT / "src"
TENANTS_DIR = REPO_ROOT / "tenants"
FIXTURE_PATH = REPO_ROOT / "tests" / "fixtures" / "baseline_report.json"
BASELINE_DIR = REPO_ROOT / "tests" / "baseline"
MANIFEST_PATH = BASELINE_DIR / "manifest.json"

RASTER_DPI = 100

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

import os  # noqa: E402

os.environ["OPENAEC_TENANTS_ROOT"] = str(TENANTS_DIR)
os.environ["OPENAEC_TENANTS_DIR"] = str(TENANTS_DIR)

import fitz  # noqa: E402
import numpy as np  # noqa: E402
from PIL import Image  # noqa: E402

from openaec_reports.core.renderer_v2 import ReportGeneratorV2  # noqa: E402


def _load_fixture() -> dict:
    with open(FIXTURE_PATH, encoding="utf-8") as f:
        return json.load(f)


def _render_fresh(tenant: str, out_pdf: Path) -> list[np.ndarray]:
    """Render de fixture opnieuw en geef een lijst van pagina-arrays terug."""
    fixture = _load_fixture()
    stationery_dir = TENANTS_DIR / tenant / "stationery"
    gen = ReportGeneratorV2(brand=tenant, tenant_slug=tenant)
    out_pdf.parent.mkdir(parents=True, exist_ok=True)
    gen.generate(dict(fixture), stationery_dir, out_pdf)

    pages: list[np.ndarray] = []
    doc = fitz.open(str(out_pdf))
    try:
        for page in doc:
            pix = page.get_pixmap(dpi=RASTER_DPI)
            arr = np.frombuffer(pix.samples, dtype=np.uint8).reshape(
                pix.height, pix.width, pix.n
            )
            # Normaliseer naar RGB (drop alpha als aanwezig)
            if pix.n == 4:
                arr = arr[:, :, :3]
            pages.append(arr.copy())
    finally:
        doc.close()
    return pages


def _load_png_array(path: Path) -> np.ndarray:
    img = Image.open(path).convert("RGB")
    return np.array(img)


def _write_diff_png(baseline: np.ndarray, fresh: np.ndarray, out_path: Path) -> None:
    """Schrijf een rood-gemarkeerde diff-afbeelding.

    Basis = fresh render (grijswaarden), afwijkende pixels worden fel rood
    overlaid zodat ze in één oogopslag zichtbaar zijn.
    """
    h = max(baseline.shape[0], fresh.shape[0])
    w = max(baseline.shape[1], fresh.shape[1])

    base_padded = np.full((h, w, 3), 255, dtype=np.uint8)
    fresh_padded = np.full((h, w, 3), 255, dtype=np.uint8)
    base_padded[: baseline.shape[0], : baseline.shape[1]] = baseline
    fresh_padded[: fresh.shape[0], : fresh.shape[1]] = fresh

    diff_mask = np.any(base_padded != fresh_padded, axis=2)

    # Grijswaarden-versie van de fresh render als achtergrond
    gray = np.array(Image.fromarray(fresh_padded).convert("L"))
    canvas = np.stack([gray, gray, gray], axis=2).astype(np.uint8)
    canvas[diff_mask] = [255, 0, 0]

    Image.fromarray(canvas).save(out_path)


def _compare_page(
    baseline_path: Path, fresh_arr: np.ndarray, tolerance: int
) -> dict:
    baseline_arr = _load_png_array(baseline_path)

    if baseline_arr.shape != fresh_arr.shape:
        return {
            "page": baseline_path.name,
            "status": "SIZE_MISMATCH",
            "baseline_shape": baseline_arr.shape,
            "fresh_shape": fresh_arr.shape,
            "diff_pixels": None,
            "diff_pct": None,
            "max_channel_diff": None,
        }

    diff = np.abs(
        baseline_arr.astype(np.int16) - fresh_arr.astype(np.int16)
    )
    pixel_diff_mask = np.any(diff != 0, axis=2)
    diff_pixels = int(np.count_nonzero(pixel_diff_mask))
    total_pixels = baseline_arr.shape[0] * baseline_arr.shape[1]
    diff_pct = (diff_pixels / total_pixels) * 100 if total_pixels else 0.0
    max_channel_diff = int(diff.max()) if diff.size else 0

    status = "OK" if diff_pixels <= tolerance else "DIFF"

    # Ruim een stale _diff.png op van een vorige (mislukte) run zodat een
    # schone diff-run ook echt schoon oogt op de filesystem.
    stale_diff_png = baseline_path.with_name(baseline_path.stem + "_diff.png")
    if status == "OK" and stale_diff_png.exists():
        stale_diff_png.unlink()

    result = {
        "page": baseline_path.name,
        "status": status,
        "diff_pixels": diff_pixels,
        "total_pixels": total_pixels,
        "diff_pct": diff_pct,
        "max_channel_diff": max_channel_diff,
    }

    if status == "DIFF":
        diff_png_path = baseline_path.with_name(
            baseline_path.stem + "_diff.png"
        )
        _write_diff_png(baseline_arr, fresh_arr, diff_png_path)
        result["diff_png"] = str(diff_png_path)

    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--tolerance",
        type=int,
        default=0,
        help="Toegestaan aantal afwijkende pixels per pagina (default: 0)",
    )
    args = parser.parse_args()

    if not MANIFEST_PATH.exists():
        print(f"FOUT: geen baseline manifest gevonden op {MANIFEST_PATH}")
        print("Draai eerst: python scripts/render_baseline.py")
        return 1

    with open(MANIFEST_PATH, encoding="utf-8") as f:
        manifest = json.load(f)

    any_diff = False
    any_error = False
    rows: list[tuple[str, str, str, str, str, str]] = []

    tmp_pdf_dir = BASELINE_DIR / "_diff_tmp"

    for report in manifest["reports"]:
        tenant = report["tenant"]
        template = report["template"]
        baseline_dir = BASELINE_DIR / tenant / template

        tmp_pdf = tmp_pdf_dir / f"{tenant}_{template}.pdf"
        try:
            fresh_pages = _render_fresh(tenant, tmp_pdf)
        except Exception as exc:  # noqa: BLE001
            print(f"[ERROR] {tenant}/{template} — render mislukt: {exc!r}")
            any_error = True
            rows.append((tenant, template, "ERROR", "-", "-", str(exc)))
            continue
        finally:
            tmp_pdf.unlink(missing_ok=True)

        expected_pages = report["pages"]
        if len(fresh_pages) != len(expected_pages):
            print(
                f"[ERROR] {tenant}/{template} — paginacount verschilt: "
                f"baseline={len(expected_pages)} fresh={len(fresh_pages)}"
            )
            any_diff = True
            rows.append(
                (
                    tenant,
                    template,
                    "PAGECOUNT",
                    f"{len(expected_pages)}",
                    f"{len(fresh_pages)}",
                    "-",
                )
            )
            continue

        for i, page_entry in enumerate(expected_pages):
            baseline_png = baseline_dir / page_entry["file"]
            cmp_result = _compare_page(baseline_png, fresh_pages[i], args.tolerance)
            status = cmp_result["status"]
            if status != "OK":
                any_diff = True
            rows.append(
                (
                    tenant,
                    template,
                    cmp_result["page"],
                    status,
                    (
                        f"{cmp_result['diff_pixels']} "
                        f"({cmp_result['diff_pct']:.4f}%)"
                        if cmp_result.get("diff_pixels") is not None
                        else "-"
                    ),
                    (
                        str(cmp_result["max_channel_diff"])
                        if cmp_result.get("max_channel_diff") is not None
                        else "-"
                    ),
                )
            )

    if tmp_pdf_dir.exists() and not any(tmp_pdf_dir.iterdir()):
        tmp_pdf_dir.rmdir()

    # --- Print compacte tabel ---
    header = ("tenant", "template", "page", "status", "diff px (%)", "max ch. diff")
    widths = [
        max(len(header[i]), max((len(str(r[i])) for r in rows), default=0))
        for i in range(len(header))
    ]
    line_fmt = "  ".join(f"{{:<{w}}}" for w in widths)
    print(line_fmt.format(*header))
    print(line_fmt.format(*["-" * w for w in widths]))
    for row in rows:
        print(line_fmt.format(*row))

    print()
    if any_error:
        print("RESULTAAT: FOUT tijdens renderen — zie hierboven.")
        return 1
    if any_diff:
        print(f"RESULTAAT: VERSCHIL gevonden (tolerance={args.tolerance} px/pagina).")
        return 1

    print(f"RESULTAAT: identiek (tolerance={args.tolerance} px/pagina).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
