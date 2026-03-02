"""Per-request tenant resolution met caching."""

from __future__ import annotations

from functools import lru_cache

from openaec_reports.core.brand import BrandLoader
from openaec_reports.core.template_loader import TemplateLoader
from openaec_reports.core.tenant import TenantConfig, detect_tenants_root


@lru_cache(maxsize=32)
def get_tenant_config(tenant_slug: str) -> TenantConfig:
    """Resolve TenantConfig voor een tenant slug. Gecached."""
    tenants_root = detect_tenants_root()
    if tenants_root and tenant_slug:
        tenant_dir = tenants_root / tenant_slug
        if tenant_dir.exists():
            return TenantConfig(tenant_dir)
    # Fallback naar default
    return TenantConfig()


@lru_cache(maxsize=32)
def get_template_loader(tenant_slug: str) -> TemplateLoader:
    """Resolve TemplateLoader voor een tenant slug. Gecached."""
    tc = get_tenant_config(tenant_slug)
    return TemplateLoader(templates_dirs=tc.templates_dirs)


@lru_cache(maxsize=32)
def get_brand_loader(tenant_slug: str) -> BrandLoader:
    """Resolve BrandLoader voor een tenant slug. Gecached."""
    tc = get_tenant_config(tenant_slug)
    return BrandLoader(tenant_config=tc)
