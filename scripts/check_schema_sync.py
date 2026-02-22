#!/usr/bin/env python3
"""Controleer dat schemas/report.schema.json en frontend/schemas/report.schema.json identiek zijn.

Gebruik als pre-commit check of CI stap:
    python scripts/check_schema_sync.py
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "schemas" / "report.schema.json"
COPY = ROOT / "frontend" / "schemas" / "report.schema.json"


def main() -> int:
    if not SOURCE.exists():
        print(f"FOUT: bron-schema niet gevonden: {SOURCE}")
        return 1
    if not COPY.exists():
        print(f"FOUT: frontend-kopie niet gevonden: {COPY}")
        return 1

    source_text = SOURCE.read_text(encoding="utf-8")
    copy_text = COPY.read_text(encoding="utf-8")

    if source_text == copy_text:
        print("OK: schemas zijn identiek")
        return 0

    print("FOUT: schemas zijn niet gesynchroniseerd!")
    print(f"  Bron:  {SOURCE}")
    print(f"  Kopie: {COPY}")
    print()
    print("Fix: kopieer het bronschema naar de frontend:")
    print(f"  cp {SOURCE} {COPY}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
