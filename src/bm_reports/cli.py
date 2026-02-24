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

    # Serve command
    serve_parser = subparsers.add_parser("serve", help="Start API server")
    serve_parser.add_argument("--host", default="0.0.0.0", help="Host adres")
    serve_parser.add_argument("--port", "-p", type=int, default=8000, help="Poort")
    serve_parser.add_argument("--reload", action="store_true", default=False, help="Auto-reload")

    # Analyze brand command
    ab_parser = subparsers.add_parser("analyze-brand", help="Analyseer brand uit referentie-PDF")
    ab_parser.add_argument("pdf", help="Pad naar referentie-PDF")
    ab_parser.add_argument(
        "--output-dir", "-o", default="./brand_analysis", help="Output directory"
    )
    ab_parser.add_argument("--brand-name", default="Brand", help="Brand weergavenaam")
    ab_parser.add_argument("--brand-slug", default="brand", help="Brand slug")
    ab_parser.add_argument("--dpi", type=int, default=150, help="DPI voor pagina renders")

    # Build brand command
    bb_parser = subparsers.add_parser("build-brand", help="Genereer complete brand directory")
    bb_parser.add_argument("--rapport", "-r", required=True, help="Pad naar referentie-rapport PDF")
    bb_parser.add_argument("--stamkaart", "-s", help="Pad naar stamkaart PDF")
    bb_parser.add_argument("--briefpapier", "-b", help="Pad naar briefpapier PDF")
    bb_parser.add_argument("--logos", "-l", help="Pad naar logo directory")
    bb_parser.add_argument("--fonts", help="Pad naar fonts directory")
    bb_parser.add_argument(
        "--base-brand", help="Pad naar bestaande brand directory (voor varianten)"
    )
    bb_parser.add_argument("--name", required=True, help="Brand weergavenaam")
    bb_parser.add_argument("--slug", required=True, help="Brand slug (machine-leesbaar)")
    bb_parser.add_argument("--output", "-o", required=True, help="Output directory")
    bb_parser.add_argument("--dpi", type=int, default=150, help="DPI voor pagina renders")

    # Extract layout command
    el_parser = subparsers.add_parser("extract-layout", help="Extraheer layout uit referentie-PDF")
    el_parser.add_argument("pdf", help="Pad naar referentie-PDF")
    el_parser.add_argument("--output", "-o", default="./extracted", help="Output directory")
    el_parser.add_argument("--dpi", type=int, default=150, help="DPI voor renders")

    # Create user command
    cu_parser = subparsers.add_parser("create-user", help="Maak een gebruiker aan")
    cu_parser.add_argument(
        "--admin", action="store_true", default=False, help="Maak een admin gebruiker"
    )
    cu_parser.add_argument("--username", "-u", default=None, help="Username (non-interactive)")
    cu_parser.add_argument("--password", "-p", default=None, help="Wachtwoord (non-interactive)")
    cu_parser.add_argument("--email", default="", help="Email adres")
    cu_parser.add_argument("--display-name", default=None, help="Weergavenaam")
    cu_parser.add_argument("--tenant", default="", help="Tenant naam")
    cu_parser.add_argument("--db", default=None, help="Pad naar auth database")

    # Create API key command
    ak_parser = subparsers.add_parser("create-api-key", help="Maak een API key aan")
    ak_parser.add_argument("--username", "-u", required=True, help="Username van de key-eigenaar")
    ak_parser.add_argument("--name", "-n", required=True, help="Beschrijving van de key")
    ak_parser.add_argument("--expires", default=None, help="Verloopdatum (ISO format)")
    ak_parser.add_argument("--db", default=None, help="Pad naar auth database")

    # Visual diff command
    vd_parser = subparsers.add_parser(
        "visual-diff", help="Vergelijk gegenereerde PDF met referentie"
    )
    vd_parser.add_argument("generated", help="Pad naar gegenereerde PDF")
    vd_parser.add_argument("reference", help="Pad naar referentie PDF")
    vd_parser.add_argument(
        "--output", "-o", default="./diffs", help="Output directory voor diff images"
    )
    vd_parser.add_argument("--dpi", type=int, default=150, help="Render DPI")

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
    elif args.command == "serve":
        _cmd_serve(args)
    elif args.command == "analyze-brand":
        _cmd_analyze_brand(args)
    elif args.command == "build-brand":
        _cmd_build_brand(args)
    elif args.command == "extract-layout":
        _cmd_extract_layout(args)
    elif args.command == "create-user":
        _cmd_create_user(args)
    elif args.command == "create-api-key":
        _cmd_create_api_key(args)
    elif args.command == "visual-diff":
        _cmd_visual_diff(args)


def _cmd_generate(args):
    """Genereer rapport vanuit CLI."""
    from bm_reports.core.engine import Report

    print(f"Genereer rapport: {args.output}")
    print(f"  Template: {args.template}")
    print(f"  Data: {args.data}")
    print(f"  Formaat: {args.format}")

    report = Report.from_json(args.data)
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


def _cmd_analyze_brand(args):
    """Analyseer brand uit referentie-PDF."""
    from bm_reports.tools import (
        analyze_brand,
        classify_pages,
        extract_pdf,
        generate_analysis_report,
        generate_brand_yaml,
    )

    pdf_path = Path(args.pdf)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    pages_dir = output_dir / "pages"

    print(f"Analyseer: {pdf_path}")
    print(f"  Output: {output_dir}")

    # Stap 1: Extractie
    print("  [1/5] PDF extractie...")
    pages = extract_pdf(pdf_path, pages_dir, dpi=args.dpi)
    page_images = [p.page_image_path for p in pages if p.page_image_path]
    print(f"         {len(pages)} pagina's geëxtraheerd")

    # Stap 2: Classificatie
    print("  [2/5] Pagina classificatie...")
    classified = classify_pages(pages)
    for cp in classified:
        if cp.page_type.value != "content":
            print(f"         p{cp.page.page_number}: {cp.page_type.value} ({cp.confidence:.0%})")

    # Stap 3: Patroon detectie
    print("  [3/5] Patroon detectie...")
    analysis = analyze_brand(classified, str(pdf_path), page_images)

    # Stap 4: YAML generatie
    print("  [4/5] Brand YAML generatie...")
    yaml_str = generate_brand_yaml(analysis, args.brand_name, args.brand_slug)
    yaml_path = output_dir / f"{args.brand_slug}.yaml"
    yaml_path.write_text(yaml_str, encoding="utf-8")
    print(f"         {yaml_path}")

    # Stap 5: Rapport
    print("  [5/5] Analyse rapport...")
    report_str = generate_analysis_report(analysis)
    report_path = output_dir / "analysis_report.md"
    report_path.write_text(report_str, encoding="utf-8")
    print(f"         {report_path}")

    # Samenvatting
    print()
    print("Samenvatting:")
    print(f"  Kleuren: {analysis.colors}")
    print(f"  Fonts:   {analysis.fonts}")
    print(f"  Marges:  {analysis.margins_mm}")
    print(f"  Footer:  {analysis.footer_zone.get('height_mm', 0)}mm")
    if analysis.styles:
        for name, style in analysis.styles.items():
            print(f"  {name}: {style.get('font', '?')} {style.get('size', '?')}pt")


def _cmd_create_user(args):
    """Maak een nieuwe gebruiker aan (interactief of non-interactive)."""
    from bm_reports.auth.models import User, UserDB, UserRole
    from bm_reports.auth.security import hash_password

    role = UserRole.admin if args.admin else UserRole.user

    # Non-interactive als --username en --password beide gezet zijn
    if args.username and args.password:
        db = UserDB(args.db)
        existing = db.get_by_username(args.username)
        if existing:
            print(f"Gebruiker '{args.username}' bestaat al (id={existing.id})")
            return

        user = User(
            username=args.username,
            email=args.email,
            display_name=args.display_name or args.username,
            role=role,
            tenant=args.tenant,
            hashed_password=hash_password(args.password),
        )
        db.create(user)
        print(f"Gebruiker aangemaakt: {user.username} (rol={role.value}, id={user.id})")
    else:
        from bm_reports.auth.seed import create_user_interactive

        create_user_interactive(db_path=args.db, role=role)


def _cmd_create_api_key(args):
    """Maak een API key aan voor een bestaande user."""
    from bm_reports.auth.api_keys import ApiKeyDB
    from bm_reports.auth.models import UserDB

    db = UserDB(args.db)
    api_db = ApiKeyDB(args.db)

    user = db.get_by_username(args.username)
    if not user:
        print(f"Fout: gebruiker '{args.username}' niet gevonden")
        raise SystemExit(1)

    api_key, plaintext = api_db.create(
        name=args.name,
        user_id=user.id,
        expires_at=args.expires,
    )

    print(f"API key aangemaakt voor {user.username}:")
    print(f"  Naam:   {api_key.name}")
    print(f"  Prefix: {api_key.key_prefix}")
    print(f"  Key:    {plaintext}")
    print()
    print("Bewaar deze key! Hij wordt maar 1x getoond.")


def _cmd_serve(args):
    """Start de FastAPI server."""
    import uvicorn

    print(f"3BM Report API server op http://{args.host}:{args.port}")
    print(f"  Docs: http://localhost:{args.port}/docs")
    uvicorn.run(
        "bm_reports.api:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
    )


def _cmd_build_brand(args):
    """Genereer complete brand directory."""
    from bm_reports.tools.brand_builder import BrandBuilder

    builder = BrandBuilder(
        output_dir=Path(args.output),
        brand_name=args.name,
        brand_slug=args.slug,
    )

    result = builder.build(
        referentie_rapport=Path(args.rapport),
        stamkaart=Path(args.stamkaart) if args.stamkaart else None,
        briefpapier=Path(args.briefpapier) if args.briefpapier else None,
        logo_dir=Path(args.logos) if args.logos else None,
        font_dir=Path(args.fonts) if args.fonts else None,
        base_brand=Path(args.base_brand) if args.base_brand else None,
        dpi=args.dpi,
    )

    print(f"Brand directory gegenereerd: {result}")


def _cmd_extract_layout(args):
    """Extraheer volledige layout uit een referentie-PDF."""
    from bm_reports.tools.layout_extractor import extract_page_layouts
    from bm_reports.tools.page_classifier import classify_pages
    from bm_reports.tools.pdf_extractor import extract_pdf

    pdf_path = Path(args.pdf)
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Extraheer layout uit: {pdf_path}")
    pages = extract_pdf(pdf_path, output_dir / "pages", dpi=args.dpi)
    classified = classify_pages(pages)
    layouts = extract_page_layouts(classified)

    for page_type, layout in layouts.items():
        print(f"\n{page_type.value.upper()} (pagina {layout.page_number}):")
        print(f"  Statische elementen: {len(layout.static_elements)}")
        print(f"  Tekst zones: {len(layout.text_zones)}")
        print(f"  Badges: {len(layout.badges)}")
        if layout.clip_polygon:
            print(f"  Clip polygon: {len(layout.clip_polygon)} punten")
        if layout.photo_rect:
            print(f"  Photo rect: {layout.photo_rect}")

    print(f"\nLayout extractie voltooid: {len(layouts)} pagina-types")


def _cmd_visual_diff(args):
    """Vergelijk gegenereerde PDF met referentie."""
    from bm_reports.tools.visual_diff import compare_pdfs, print_diff_report

    generated = Path(args.generated)
    reference = Path(args.reference)
    output_dir = Path(args.output)

    print(f"Vergelijk: {generated.name} vs {reference.name}")
    diffs = compare_pdfs(generated, reference, output_dir, dpi=args.dpi)
    print_diff_report(diffs)


if __name__ == "__main__":
    main()
