"""CLI — Command line interface voor rapport generatie."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def main():
    """Hoofdentrypoint voor de CLI.

    Usage:
        bm-report generate --template structural --data project.json --output rapport.pdf
        bm-report templates --list
        bm-report validate --data project.json
    """
    parser = argparse.ArgumentParser(
        prog="bm-report",
        description="3BM Report Generator — Professionele engineering rapporten",
    )
    subparsers = parser.add_subparsers(dest="command", help="Beschikbare commando's")

    # Generate command
    gen_parser = subparsers.add_parser("generate", help="Genereer een rapport")
    gen_parser.add_argument("--template", "-t", required=True, help="Template naam")
    gen_parser.add_argument("--data", "-d", required=True, help="JSON data bestand")
    gen_parser.add_argument("--output", "-o", required=True, help="Output PDF pad")
    gen_parser.add_argument("--format", "-f", default="A4", choices=["A4", "A3"])

    # Templates command
    tmpl_parser = subparsers.add_parser("templates", help="Beheer templates")
    tmpl_parser.add_argument("--list", action="store_true", help="Toon beschikbare templates")

    # Validate command
    val_parser = subparsers.add_parser("validate", help="Valideer data bestand")
    val_parser.add_argument("--data", "-d", required=True, help="JSON data bestand")

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(1)

    if args.command == "generate":
        _cmd_generate(args)
    elif args.command == "templates":
        _cmd_templates(args)
    elif args.command == "validate":
        _cmd_validate(args)


def _cmd_generate(args):
    """Genereer rapport vanuit CLI."""
    from bm_reports.core.engine import Report
    from bm_reports.core.document import A4, A3

    fmt = A4 if args.format == "A4" else A3

    print(f"Genereer rapport: {args.output}")
    print(f"  Template: {args.template}")
    print(f"  Data: {args.data}")
    print(f"  Formaat: {args.format}")

    report = Report.from_json(args.data, template=args.template)
    output = report.build(args.output)
    print(f"  ✓ Rapport gegenereerd: {output}")


def _cmd_templates(args):
    """Toon beschikbare templates."""
    templates_dir = Path(__file__).parent / "assets" / "templates"
    if not templates_dir.exists():
        print("Geen templates gevonden.")
        return

    print("Beschikbare templates:")
    for tmpl in sorted(templates_dir.glob("*.yaml")):
        print(f"  - {tmpl.stem}")


def _cmd_validate(args):
    """Valideer JSON data bestand."""
    from bm_reports.data.json_adapter import JsonAdapter

    adapter = JsonAdapter(args.data)
    errors = adapter.validate()

    if errors:
        print(f"Validatie fouten ({len(errors)}):")
        for err in errors:
            print(f"  ✗ {err}")
        sys.exit(1)
    else:
        print("✓ Data is geldig.")


if __name__ == "__main__":
    main()
