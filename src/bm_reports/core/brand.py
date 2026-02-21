"""Brand systeem — YAML-configureerbare merken met kleuren, fonts, header/footer."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path

import yaml

logger = logging.getLogger(__name__)

# Standaard locatie van brand bestanden binnen het package
BRANDS_DIR = Path(__file__).parent.parent / "assets" / "brands"


@dataclass
class ElementConfig:
    """Enkel tekenbaar element in header/footer.

    Attrs:
        type: Element type ("rect", "text", "image", "line").
        x: Positie in mm vanaf linker paginarand.
        y: Positie in mm vanaf onderkant van de zone.
        width: Breedte in mm.
        height: Hoogte in mm.
        fill: Vulkleur — "$primary" of "#38BDA0".
        color: Tekst/lijn kleur — "$text" of hex.
        stroke: Outline kleur.
        stroke_width: Lijndikte in points.
        content: Tekst met {variabelen} (bijv. "{page}").
        src: Afbeelding pad relatief t.o.v. assets/.
        font: Font referentie — "$heading" of "Helvetica-Bold".
        size: Font grootte in points.
        align: Tekst uitlijning ("left", "center", "right").
    """

    type: str = ""
    x: float = 0.0
    y: float = 0.0
    width: float = 0.0
    height: float = 0.0
    fill: str = ""
    color: str = ""
    stroke: str = ""
    stroke_width: float = 0.5
    content: str = ""
    src: str = ""
    font: str = ""
    size: float = 0.0
    align: str = "left"


@dataclass
class ZoneConfig:
    """Header of footer zone configuratie.

    Attrs:
        height: Hoogte in mm. 0 betekent geen zone (wordt overgeslagen).
        elements: Lijst van tekenbare elementen.
    """

    height: float = 0.0
    elements: list[ElementConfig] = field(default_factory=list)


@dataclass
class StationeryPageConfig:
    """Stationery configuratie per paginatype."""

    source: str = ""
    header_footer: str | None = None
    text_zones: list[dict] = field(default_factory=list)
    content_frame: dict | None = None


@dataclass
class BrandConfig:
    """Volledige brand configuratie.

    Attrs:
        name: Weergavenaam van het merk.
        slug: Machine-leesbare identifier.
        colors: Kleurenpalet (naam → hex waarde).
        fonts: Font mapping (naam → font naam).
        header: Header zone configuratie.
        footer: Footer zone configuratie.
        logos: Logo mapping (naam → relatief pad).
        stationery: Achtergrond-templates per paginatype.
        modules: Module-specifieke styling (table, calculation, etc.).
        brand_dir: Directory van het YAML bestand (voor relatieve paden).
    """

    name: str = "Default"
    slug: str = "default"
    colors: dict[str, str] = field(default_factory=dict)
    fonts: dict[str, str] = field(default_factory=dict)
    header: ZoneConfig = field(default_factory=ZoneConfig)
    footer: ZoneConfig = field(default_factory=ZoneConfig)
    logos: dict[str, str] = field(default_factory=dict)
    contact: dict[str, str] = field(default_factory=dict)
    styles: dict[str, dict] = field(default_factory=dict)
    pages: dict[str, dict] = field(default_factory=dict)
    stationery: dict[str, StationeryPageConfig] = field(default_factory=dict)
    modules: dict[str, dict] = field(default_factory=dict)
    brand_dir: Path | None = None


def _parse_elements(raw_elements: list[dict] | None) -> list[ElementConfig]:
    """Parseer een lijst van ruwe element dicts naar ElementConfig objecten."""
    if not raw_elements:
        return []
    elements = []
    for elem_data in raw_elements:
        elements.append(ElementConfig(
            type=elem_data.get("type", ""),
            x=float(elem_data.get("x", 0)),
            y=float(elem_data.get("y", 0)),
            width=float(elem_data.get("width", 0)),
            height=float(elem_data.get("height", 0)),
            fill=str(elem_data.get("fill", "")),
            color=str(elem_data.get("color", "")),
            stroke=str(elem_data.get("stroke", "")),
            stroke_width=float(elem_data.get("stroke_width", 0.5)),
            content=str(elem_data.get("content", "")),
            src=str(elem_data.get("src", "")),
            font=str(elem_data.get("font", "")),
            size=float(elem_data.get("size", 0)),
            align=str(elem_data.get("align", "left")),
        ))
    return elements


def _parse_zone(raw_zone: dict | None) -> ZoneConfig:
    """Parseer een ruwe zone dict naar ZoneConfig."""
    if not raw_zone:
        return ZoneConfig()
    return ZoneConfig(
        height=float(raw_zone.get("height", 0)),
        elements=_parse_elements(raw_zone.get("elements")),
    )


class BrandLoader:
    """Laad en parseer YAML brand configuraties.

    Volgt hetzelfde patroon als TemplateLoader: zoek in assets/brands/
    of een custom directory. Ondersteunt TenantConfig voor multi-tenant.

    Usage:
        loader = BrandLoader()
        brand = loader.load("3bm_cooperatie")
        default = loader.load_default()
        available = loader.list_brands()

        # Met TenantConfig:
        from bm_reports.core.tenant import TenantConfig
        loader = BrandLoader(tenant_config=TenantConfig("/data/tenants/3bm"))
    """

    def __init__(
        self,
        brands_dir: Path | None = None,
        tenant_config: "TenantConfig | None" = None,
    ):
        self._tenant_config = tenant_config
        self.brands_dir = brands_dir or BRANDS_DIR

    def load(self, name: str | None = None) -> BrandConfig:
        """Laad een brand configuratie op naam.

        Bij tenant_config: als name niet opgegeven, laad tenant brand.yaml.
        Anders zoek op naam in brands_dir.

        Args:
            name: Brand naam (zonder .yaml extensie). None = tenant default.

        Returns:
            BrandConfig met de geparseerde brand data.

        Raises:
            FileNotFoundError: Als het brand bestand niet gevonden wordt.
        """
        # Als tenant config beschikbaar en geen specifieke naam → tenant brand
        if name is None and self._tenant_config:
            path = self._tenant_config.brand_path
        elif name is None:
            path = self.brands_dir / "default.yaml"
        else:
            # Check tenant brand path eerst als naam overeenkomt
            if self._tenant_config:
                tenant_brand = self._tenant_config.brand_path
                if tenant_brand.exists():
                    # Lees slug uit tenant brand om te matchen
                    try:
                        with tenant_brand.open("r", encoding="utf-8") as f:
                            data = yaml.safe_load(f)
                        brand_info = data.get("brand", {}) if data else {}
                        slug = brand_info.get("slug", "")
                        if slug == name or tenant_brand.stem == name or name == "brand":
                            path = tenant_brand
                        else:
                            path = self._resolve_path(name)
                    except Exception:
                        path = self._resolve_path(name)
                else:
                    path = self._resolve_path(name)
            else:
                path = self._resolve_path(name)

        if not path.exists():
            raise FileNotFoundError(
                f"Brand '{name}' niet gevonden in {self.brands_dir}"
            )

        with path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        if data is None:
            data = {}

        brand_info = data.get("brand", {})

        # Stationery parsen
        stationery = {}
        for page_type, spec in data.get("stationery", {}).items():
            stationery[page_type] = StationeryPageConfig(
                source=spec.get("source", ""),
                header_footer=spec.get("header_footer"),
                text_zones=spec.get("text_zones", []),
                content_frame=spec.get("content_frame"),
            )

        return BrandConfig(
            name=brand_info.get("name", name),
            slug=brand_info.get("slug", name),
            colors=data.get("colors", {}),
            fonts=data.get("fonts", {}),
            header=_parse_zone(data.get("header")),
            footer=_parse_zone(data.get("footer")),
            logos=data.get("logos", {}),
            contact=data.get("contact", {}),
            styles=data.get("styles", {}),
            pages=data.get("pages", {}),
            stationery=stationery,
            modules=data.get("modules", {}),
            brand_dir=path.parent,
        )

    def load_default(self) -> BrandConfig:
        """Laad de standaard brand configuratie.

        Returns:
            BrandConfig voor het 'default' merk.
        """
        return self.load("default")

    def list_brands(self) -> list[dict[str, str]]:
        """Lijst alle beschikbare brands.

        Bij tenant_config: toont tenant brand + package brands (dedup op slug).

        Returns:
            Lijst van dicts met 'name' en 'slug' per brand.
        """
        brands = []
        seen_slugs: set[str] = set()

        # Tenant brand eerst (als beschikbaar)
        if self._tenant_config:
            tenant_brand = self._tenant_config.brand_path
            if tenant_brand.exists():
                try:
                    with tenant_brand.open("r", encoding="utf-8") as f:
                        data = yaml.safe_load(f)
                    brand_info = data.get("brand", {}) if data else {}
                    slug = brand_info.get("slug", tenant_brand.stem)
                    brands.append({
                        "name": brand_info.get("name", tenant_brand.stem),
                        "slug": slug,
                    })
                    seen_slugs.add(slug)
                except yaml.YAMLError:
                    pass

        # Package brands
        if self.brands_dir.exists():
            for path in sorted(self.brands_dir.glob("*.yaml")):
                try:
                    with path.open("r", encoding="utf-8") as f:
                        data = yaml.safe_load(f)
                    brand_info = data.get("brand", {}) if data else {}
                    slug = brand_info.get("slug", path.stem)
                    if slug in seen_slugs:
                        continue
                    seen_slugs.add(slug)
                    brands.append({
                        "name": brand_info.get("name", path.stem),
                        "slug": slug,
                    })
                except yaml.YAMLError:
                    slug = path.stem
                    if slug not in seen_slugs:
                        seen_slugs.add(slug)
                        brands.append({"name": path.stem, "slug": slug})

        return brands

    def _resolve_path(self, name: str) -> Path:
        """Resolve brand naam naar bestandspad.

        Ondersteunt zowel single-file als directory layout:
        - brands/3bm_cooperatie.yaml (legacy)
        - brands/3bm-cooperatie/brand.yaml (v2 directory)
        """
        if name.endswith(".yaml"):
            return self.brands_dir / name
        # Probeer eerst directory layout
        dir_path = self.brands_dir / name / "brand.yaml"
        if dir_path.exists():
            return dir_path
        # Fallback naar single file
        return self.brands_dir / f"{name}.yaml"
