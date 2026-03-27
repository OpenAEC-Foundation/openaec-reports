"""Genereer PDF's van alle voorbeeld JSON-bestanden.

Detecteert automatisch de juiste engine (V1, V2, Template Engine)
op basis van tenant en template type.

Gebruik:
    python examples/scripts/generate_all_examples.py
    python examples/scripts/generate_all_examples.py --only customer
    python examples/scripts/generate_all_examples.py --only default/structural_report
    python examples/scripts/generate_all_examples.py --list
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

# Zorg dat het package importeerbaar is
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

EXAMPLES_DIR = PROJECT_ROOT / "examples"
OUTPUT_DIR = PROJECT_ROOT / "output" / "examples"
TENANTS_DIR = PROJECT_ROOT / "tenants"

# Tenant folders in examples/
TENANT_DIRS = ["default", "customer", "openaec_foundation"]

# Template Engine (V3) templates — pages bevat list[dict]
# Alle andere zijn legacy (V1/V2)
TEMPLATE_ENGINE_TEMPLATES = {
    "bic_rapport",
    "bic_factuur",
    "customer_bic_rapport",
    "customer_bic_factuur",
}

# Block types die alleen V2 renderer ondersteunt
V2_ONLY_BLOCKS = {"heading_2", "bullet_list"}


def discover_examples(filter_str: str | None = None) -> list[dict]:
    """Ontdek alle voorbeeld JSON-bestanden met metadata.

    Returns:
        List van dicts met keys: path, tenant, template, engine
    """
    examples = []

    for tenant_dir_name in TENANT_DIRS:
        tenant_path = EXAMPLES_DIR / tenant_dir_name
        if not tenant_path.is_dir():
            continue

        for json_file in sorted(tenant_path.glob("*.json")):
            rel = f"{tenant_dir_name}/{json_file.stem}"

            if filter_str and filter_str not in rel:
                continue

            with open(json_file, encoding="utf-8") as f:
                data = json.load(f)

            template = data.get("template", "structural")
            tenant = data.get("tenant", tenant_dir_name)
            engine = _detect_engine(data, template, json_file)

            examples.append({
                "path": json_file,
                "tenant": tenant,
                "template": template,
                "engine": engine,
                "rel": rel,
            })

    return examples


def _detect_engine(data: dict, template: str, path: Path) -> str:
    """Detecteer welke engine nodig is: 'template_engine', 'v2', of 'v1'."""
    # Template Engine als template in bekende V3 set
    if template in TEMPLATE_ENGINE_TEMPLATES:
        return "template_engine"

    # Check of het JSON bestand V2-only block types bevat
    raw = json.dumps(data)
    for block_type in V2_ONLY_BLOCKS:
        if f'"type": "{block_type}"' in raw or f'"type":"{block_type}"' in raw:
            return "v2"

    return "v1"


def generate_v1(example: dict) -> Path:
    """Genereer via Report.from_dict() (V1 ReportLab engine)."""
    from openaec_reports.core.engine import Report

    with open(example["path"], encoding="utf-8") as f:
        data = json.load(f)

    # Brand instellen op basis van tenant
    brand = example["tenant"]
    os.environ["OPENAEC_TENANT_DIR"] = str(TENANTS_DIR / brand)

    output_path = OUTPUT_DIR / example["tenant"] / f"{example['path'].stem}.pdf"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    report = Report.from_dict(data, brand=brand)
    report.build(str(output_path))
    return output_path


def generate_v2(example: dict) -> Path:
    """Genereer via ReportGeneratorV2 (PyMuPDF renderer)."""
    from openaec_reports.core.renderer_v2 import ReportGeneratorV2

    with open(example["path"], encoding="utf-8") as f:
        data = json.load(f)

    brand = example["tenant"]
    os.environ["OPENAEC_TENANT_DIR"] = str(TENANTS_DIR / brand)

    output_path = OUTPUT_DIR / example["tenant"] / f"{example['path'].stem}.pdf"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    stationery_dir = TENANTS_DIR / brand / "stationery"
    gen = ReportGeneratorV2(brand=brand)
    gen.generate(data, stationery_dir, output_path)
    return output_path


def generate_template_engine(example: dict) -> Path:
    """Genereer via TemplateEngine (template-driven PyMuPDF)."""
    from openaec_reports.core.template_engine import TemplateEngine

    with open(example["path"], encoding="utf-8") as f:
        data = json.load(f)

    tenant = example["tenant"]
    template = example["template"]

    # Strip tenant prefix als die in de template naam zit
    # bijv. "customer_bic_factuur" → "bic_factuur" (YAML heet bic_factuur.yaml)
    prefix = f"{tenant}_"
    if template.startswith(prefix):
        template = template[len(prefix):]

    os.environ["OPENAEC_TENANT_DIR"] = str(TENANTS_DIR / tenant)

    output_path = OUTPUT_DIR / tenant / f"{example['path'].stem}.pdf"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    engine = TemplateEngine(tenants_dir=TENANTS_DIR)
    engine.build(
        template_name=template,
        tenant=tenant,
        data=data,
        output_path=str(output_path),
    )
    return output_path


GENERATORS = {
    "v1": generate_v1,
    "v2": generate_v2,
    "template_engine": generate_template_engine,
}

ENGINE_LABELS = {
    "v1": "V1 (ReportLab)",
    "v2": "V2 (PyMuPDF)",
    "template_engine": "Template Engine",
}


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Genereer PDF's van alle voorbeeld JSON-bestanden."
    )
    parser.add_argument(
        "--only",
        help="Filter op tenant of bestandsnaam (bijv. 'customer' of 'default/structural')",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="Toon alleen de gevonden voorbeelden zonder te genereren",
    )
    args = parser.parse_args()

    examples = discover_examples(args.only)

    if not examples:
        print(f"Geen voorbeelden gevonden (filter: {args.only})")
        sys.exit(1)

    # Header
    print(f"\n{'='*70}")
    print(f"  OpenAEC Reports — Voorbeeld PDF Generator")
    print(f"  {len(examples)} bestanden gevonden")
    print(f"{'='*70}\n")

    # Tabel
    print(f"  {'#':<4} {'Bestand':<45} {'Engine':<20}")
    print(f"  {'-'*4} {'-'*45} {'-'*20}")
    for i, ex in enumerate(examples, 1):
        print(f"  {i:<4} {ex['rel']:<45} {ENGINE_LABELS[ex['engine']]:<20}")

    if args.list:
        print()
        return

    print(f"\n  Output: {OUTPUT_DIR}\n")
    print(f"{'='*70}\n")

    # Genereer
    results = []
    for i, ex in enumerate(examples, 1):
        label = f"[{i}/{len(examples)}]"
        print(f"  {label} {ex['rel']} ({ENGINE_LABELS[ex['engine']]})")
        print(f"         ", end="", flush=True)

        generator = GENERATORS[ex["engine"]]
        t0 = time.perf_counter()

        try:
            output_path = generator(ex)
            elapsed = time.perf_counter() - t0
            size_kb = output_path.stat().st_size / 1024
            print(f"OK  ({elapsed:.1f}s, {size_kb:.0f} KB) -> {output_path.name}")
            results.append({"status": "ok", "example": ex, "time": elapsed})
        except Exception as e:
            elapsed = time.perf_counter() - t0
            print(f"FOUT ({elapsed:.1f}s): {e}")
            results.append({"status": "error", "example": ex, "error": str(e)})

    # Samenvatting
    ok = sum(1 for r in results if r["status"] == "ok")
    fail = sum(1 for r in results if r["status"] == "error")
    total_time = sum(r.get("time", 0) for r in results)

    print(f"\n{'='*70}")
    print(f"  Resultaat: {ok} geslaagd, {fail} mislukt ({total_time:.1f}s totaal)")

    if fail:
        print(f"\n  Mislukt:")
        for r in results:
            if r["status"] == "error":
                print(f"    - {r['example']['rel']}: {r['error']}")

    print(f"{'='*70}\n")
    sys.exit(1 if fail else 0)


if __name__ == "__main__":
    main()
