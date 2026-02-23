"""pyRevit voorbeeld: rapport genereren via de 3BM Report API.

Dit script laat zien hoe je vanuit pyRevit (CPython 3.8+) een rapport
genereert via de API. Het werkt ook standalone buiten Revit.

Gebruik in pyRevit:
    1. Kopieer dit script naar je pyRevit extension
    2. Pas API_URL en credentials aan
    3. Voer uit via pyRevit button

Gebruik standalone:
    python examples/pyrevit_generate_report.py
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

# --- Configuratie ---

API_URL = os.environ.get("BM_REPORT_API", "https://report.3bm.co.nl")
USERNAME = os.environ.get("BM_REPORT_USER", "")
PASSWORD = os.environ.get("BM_REPORT_PASS", "")


# ============================================================
# API Client
# ============================================================


class ReportApiClient:
    """Eenvoudige API client voor de 3BM Report Generator.

    Gebruikt Bearer token authenticatie (geen cookies nodig).
    Compatibel met pyRevit CPython 3.8+ en standaard Python 3.10+.

    Args:
        base_url: Basis URL van de API (bijv. "https://report.3bm.co.nl").
    """

    def __init__(self, base_url: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.token: str | None = None
        # Gebruik urllib (stdlib) zodat 'requests' geen vereiste is
        import urllib.request
        self._urllib = urllib.request

    def login(self, username: str, password: str) -> dict:
        """Log in en bewaar het Bearer token.

        Args:
            username: Gebruikersnaam.
            password: Wachtwoord.

        Returns:
            User dict uit de API response.

        Raises:
            RuntimeError: Bij login fout.
        """
        data = json.dumps({"username": username, "password": password})
        req = self._urllib.Request(
            f"{self.base_url}/api/auth/login",
            data=data.encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with self._urllib.urlopen(req) as resp:
                body = json.loads(resp.read().decode("utf-8"))
        except Exception as e:
            raise RuntimeError(f"Login mislukt: {e}") from e

        self.token = body.get("token")
        if not self.token:
            raise RuntimeError("Geen token ontvangen — controleer API versie")

        return body.get("user", {})

    def _auth_headers(self) -> dict[str, str]:
        """Retourneer headers met Bearer token.

        Returns:
            Dict met Authorization en Content-Type headers.

        Raises:
            RuntimeError: Als niet ingelogd.
        """
        if not self.token:
            raise RuntimeError("Niet ingelogd — roep login() eerst aan")
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }

    def get_templates(self) -> list[dict]:
        """Haal beschikbare templates op.

        Returns:
            Lijst van template dicts.
        """
        req = self._urllib.Request(
            f"{self.base_url}/api/templates",
            headers=self._auth_headers(),
        )
        with self._urllib.urlopen(req) as resp:
            body = json.loads(resp.read().decode("utf-8"))
        return body.get("templates", [])

    def validate(self, report_data: dict) -> dict:
        """Valideer rapport data tegen het schema.

        Args:
            report_data: Rapport definitie als dict.

        Returns:
            Validatie resultaat met 'valid' en 'errors'.
        """
        data = json.dumps(report_data)
        req = self._urllib.Request(
            f"{self.base_url}/api/validate",
            data=data.encode("utf-8"),
            headers=self._auth_headers(),
            method="POST",
        )
        with self._urllib.urlopen(req) as resp:
            return json.loads(resp.read().decode("utf-8"))

    def generate_pdf(self, report_data: dict, output_path: str | Path) -> Path:
        """Genereer een PDF rapport.

        Args:
            report_data: Rapport definitie als dict.
            output_path: Pad waar de PDF opgeslagen wordt.

        Returns:
            Path naar het gegenereerde PDF bestand.
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        data = json.dumps(report_data)
        req = self._urllib.Request(
            f"{self.base_url}/api/generate/v2",
            data=data.encode("utf-8"),
            headers=self._auth_headers(),
            method="POST",
        )

        with self._urllib.urlopen(req) as resp:
            pdf_bytes = resp.read()

        output_path.write_bytes(pdf_bytes)
        return output_path


# ============================================================
# Voorbeeld: rapport genereren
# ============================================================


def build_example_report() -> dict:
    """Bouw een voorbeeld rapport definitie.

    In een echte pyRevit integratie zou je hier data uit het
    Revit model halen (projectinfo, elementen, berekeningen).

    Returns:
        Rapport definitie dict conform het JSON schema.
    """
    return {
        "template": "structural",
        "project": "Voorbeeld Woonhuis",
        "project_number": "2026-001",
        "client": "Particuliere Opdrachtgever",
        "address": "Voorbeeldstraat 1, Amsterdam",
        "date": "2026-02-23",
        "author": "Ing. J. de Vries",
        "cover": {
            "title": "Constructieve berekening",
            "subtitle": "Hoofddraagconstructie",
        },
        "sections": [
            {
                "title": "Uitgangspunten",
                "level": 1,
                "content": [
                    {
                        "type": "paragraph",
                        "text": "Dit rapport beschrijft de constructieve "
                        "berekening voor het project Voorbeeld Woonhuis.",
                    },
                    {
                        "type": "paragraph",
                        "text": "Alle berekeningen zijn uitgevoerd conform "
                        "de Eurocode (NEN-EN 1990 t/m 1999).",
                    },
                ],
            },
            {
                "title": "Staalligger L1",
                "level": 1,
                "content": [
                    {
                        "type": "paragraph",
                        "text": "HEA 200, staal S235, overspanning 6.0 m.",
                    },
                    {
                        "type": "calculation",
                        "label": "Veldmoment",
                        "formula": "M_Ed = q × L² / 8",
                        "variables": "q = 8.7 kN/m, L = 6.0 m",
                        "result": "39.1 kNm",
                        "unity_check": 0.58,
                        "conclusion": "VOLDOET",
                    },
                    {
                        "type": "check",
                        "label": "Buiging HEA 200",
                        "norm": "NEN-EN 1993-1-1",
                        "required_value": 39.1,
                        "calculated_value": 67.4,
                        "unit": "kNm",
                        "result": "pass",
                    },
                ],
            },
        ],
    }


def main() -> None:
    """Hoofdfunctie: login, valideer, en genereer rapport."""
    username = USERNAME
    password = PASSWORD

    if not username or not password:
        print("Stel BM_REPORT_USER en BM_REPORT_PASS in als environment variables,")
        print("of pas USERNAME en PASSWORD aan in dit script.")
        print()
        print("Voorbeeld:")
        print('  set BM_REPORT_USER=mijn_gebruiker')
        print('  set BM_REPORT_PASS=mijn_wachtwoord')
        print('  python examples/pyrevit_generate_report.py')
        sys.exit(1)

    # 1. Maak client en log in
    client = ReportApiClient(API_URL)
    print(f"Verbinden met {API_URL}...")
    user = client.login(username, password)
    print(f"Ingelogd als: {user.get('username')} ({user.get('role')})")

    # 2. Toon beschikbare templates
    templates = client.get_templates()
    print(f"\nBeschikbare templates: {len(templates)}")
    for t in templates:
        print(f"  - {t['name']} ({t.get('report_type', '?')})")

    # 3. Bouw rapport data
    report_data = build_example_report()

    # 4. Valideer
    print("\nValidatie...")
    result = client.validate(report_data)
    if result.get("valid"):
        print("  OK — data is geldig")
    else:
        print("  FOUTEN:")
        for err in result.get("errors", []):
            print(f"    - {err.get('path')}: {err.get('message')}")
        sys.exit(1)

    # 5. Genereer PDF
    output = Path(__file__).parent.parent / "output" / "pyrevit_voorbeeld.pdf"
    print(f"\nPDF genereren...")
    pdf_path = client.generate_pdf(report_data, output)
    print(f"Rapport opgeslagen: {pdf_path}")


if __name__ == "__main__":
    main()
