"""Tenant CORS configuratie loader + origin matcher.

Leest `tenants/<slug>/tenant.yaml` voor elke tenant en bouwt een mapping van
origin → tenant en een union-set van alle toegestane origins. Wordt door
``TenantAwareCORSMiddleware`` gebruikt voor per-request origin matching.

Schema (zie ``C:/GitHub/openaec-tenants/tenants/_schema.md``):

    slug: <str>
    display_name: <str>
    active: <bool>   # default true bij missend veld
    cors:
      allowed_origins: [<str>, ...]
      allowed_origins_dev: [<str>, ...]

Fallback-gedrag (conform schema):
- Missende ``tenant.yaml``: WARN + skip (niet crashen).
- Malformed YAML: WARN + behandel als ``active: false`` (skip).
- Ontbrekende velden: ``active`` default true, ``cors`` default leeg.
- Invalide origin (geen protocol, trailing slash, ...): WARN + skip die origin.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)

_VALID_PROTOCOLS = ("http://", "https://")


def _validate_origin(origin: str, *, slug: str) -> bool:
    """Basis-validatie op een origin-string volgens schema-regels.

    Controleert:
    - Protocol http:// of https://
    - Geen trailing slash
    - Lowercase (origin als geheel)
    - Geen wildcards (``*``)

    Logt een warning bij rejection en retourneert ``False``.
    """
    if not isinstance(origin, str) or not origin:
        logger.warning("tenant %s: lege/niet-string origin genegeerd: %r", slug, origin)
        return False
    if not origin.startswith(_VALID_PROTOCOLS):
        logger.warning(
            "tenant %s: origin %r heeft geen http(s):// protocol — skip", slug, origin
        )
        return False
    if origin.endswith("/"):
        logger.warning(
            "tenant %s: origin %r eindigt op trailing slash — skip", slug, origin
        )
        return False
    if "*" in origin:
        logger.warning(
            "tenant %s: origin %r bevat wildcard — skip (niet ondersteund)",
            slug,
            origin,
        )
        return False
    if origin != origin.lower():
        logger.warning(
            "tenant %s: origin %r is niet lowercase — skip", slug, origin
        )
        return False
    return True


def _extract_origins(
    cors_block: Any, *, slug: str, include_dev: bool
) -> set[str]:
    """Extract en valideer origins uit het ``cors`` block van tenant.yaml."""
    origins: set[str] = set()
    if not isinstance(cors_block, dict):
        if cors_block is not None:
            logger.warning(
                "tenant %s: cors block is geen mapping (%s) — skip", slug, type(cors_block).__name__
            )
        return origins

    prod = cors_block.get("allowed_origins") or []
    if not isinstance(prod, list):
        logger.warning("tenant %s: allowed_origins is geen list — skip", slug)
        prod = []
    for origin in prod:
        if _validate_origin(origin, slug=slug):
            origins.add(origin)

    if include_dev:
        dev = cors_block.get("allowed_origins_dev") or []
        if not isinstance(dev, list):
            logger.warning(
                "tenant %s: allowed_origins_dev is geen list — skip", slug
            )
            dev = []
        for origin in dev:
            if _validate_origin(origin, slug=slug):
                origins.add(origin)

    return origins


def _load_single_tenant(
    tenant_dir: Path, *, include_dev: bool
) -> tuple[str, set[str]] | None:
    """Laad één ``tenant.yaml``.

    Returns:
        (slug, origins) tuple, of ``None`` bij skip/fout.
    """
    tenant_yaml = tenant_dir / "tenant.yaml"
    dir_slug = tenant_dir.name

    if not tenant_yaml.exists():
        logger.warning(
            "tenant %s: geen tenant.yaml gevonden — skip (CORS-config niet geladen)",
            dir_slug,
        )
        return None

    try:
        with tenant_yaml.open("r", encoding="utf-8") as fh:
            data = yaml.safe_load(fh)
    except (yaml.YAMLError, OSError) as exc:
        logger.warning(
            "tenant %s: tenant.yaml is malformed of niet leesbaar (%s) — behandel als inactive",
            dir_slug,
            exc,
        )
        return None

    if not isinstance(data, dict):
        logger.warning(
            "tenant %s: tenant.yaml is geen mapping — behandel als inactive",
            dir_slug,
        )
        return None

    # Actief check: default true als veld mist
    active = data.get("active", True)
    if active is False:
        logger.info("tenant %s: active=false — skip", dir_slug)
        return None

    slug = data.get("slug") or dir_slug
    if not isinstance(slug, str):
        logger.warning(
            "tenant %s: slug veld is geen string (%r) — fallback op dir-naam",
            dir_slug,
            slug,
        )
        slug = dir_slug

    if slug != dir_slug:
        logger.warning(
            "tenant directory %s heeft afwijkende slug %r in tenant.yaml",
            dir_slug,
            slug,
        )

    origins = _extract_origins(data.get("cors"), slug=slug, include_dev=include_dev)
    return slug, origins


def load_tenant_cors_configs(
    tenants_root: Path, include_dev: bool
) -> dict[str, set[str]]:
    """Scan ``tenants_root`` voor subdirectories en laad elk ``tenant.yaml``.

    Args:
        tenants_root: Parent directory met alle tenant-subdirectories.
        include_dev: Indien ``True``, ook ``allowed_origins_dev`` meenemen.

    Returns:
        Mapping ``{slug: set_of_allowed_origins}``. Alleen actieve tenants met
        een leesbare ``tenant.yaml`` komen terug. Tenants zonder origins
        (lege set) komen wel mee — die accepteren dan simpelweg geen CORS.
    """
    configs: dict[str, set[str]] = {}
    if not tenants_root.exists() or not tenants_root.is_dir():
        logger.warning(
            "tenants_root %s bestaat niet of is geen directory — geen tenants geladen",
            tenants_root,
        )
        return configs

    for entry in sorted(tenants_root.iterdir()):
        if not entry.is_dir():
            continue
        # Skip verborgen mappen en ``_`` prefixed (docs/schema)
        if entry.name.startswith((".", "_")):
            continue
        result = _load_single_tenant(entry, include_dev=include_dev)
        if result is None:
            continue
        slug, origins = result
        configs[slug] = origins
        logger.info(
            "tenant %s: %d toegestane origin(s) geladen", slug, len(origins)
        )

    return configs


def build_origin_to_tenant_map(
    configs: dict[str, set[str]],
) -> dict[str, str]:
    """Inverteer ``{slug: origins}`` naar ``{origin: slug}``.

    Bij dubbele origin (twee tenants claimen dezelfde origin) logt een warning
    en de laatst-geziene tenant wint. In de praktijk mag dit niet voorkomen,
    maar we blokkeren er niet op — dev/localhost-origins kunnen best overlappen
    en dat is expected (zie ``allowed_origins_dev``).
    """
    origin_map: dict[str, str] = {}
    for slug, origins in configs.items():
        for origin in origins:
            existing = origin_map.get(origin)
            if existing and existing != slug:
                logger.warning(
                    "origin %s wordt door meerdere tenants geclaimd (%s + %s) — "
                    "laatste wint (%s)",
                    origin,
                    existing,
                    slug,
                    slug,
                )
            origin_map[origin] = slug
    return origin_map


def build_allowed_origins_set(
    configs: dict[str, set[str]],
) -> frozenset[str]:
    """Union van alle tenant origins — voor snelle membership check."""
    result: set[str] = set()
    for origins in configs.values():
        result.update(origins)
    return frozenset(result)
