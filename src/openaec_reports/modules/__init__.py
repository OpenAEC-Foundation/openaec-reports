"""Module registry voor tenant-specifieke content modules.

Core modules zijn universeel beschikbaar. Tenant modules zijn alleen
beschikbaar voor specifieke tenants. Bij lookup wordt eerst
tenant-specifiek gezocht, dan core.
"""

from __future__ import annotations

from .base import ContentModule, ModuleConfig


class ModuleRegistry:
    """Registratie van beschikbare content block types.

    Core modules zijn universeel beschikbaar.
    Tenant modules zijn alleen beschikbaar voor specifieke tenants.

    Usage::

        ModuleRegistry.register_core("paragraph", ParagraphModule)
        ModuleRegistry.register_tenant("acme", "invoice_table", InvoiceTableModule)

        cls = ModuleRegistry.get("invoice_table", tenant="acme")
        cls = ModuleRegistry.get("paragraph")  # core fallback
    """

    _core_modules: dict[str, type] = {}
    _tenant_modules: dict[str, dict[str, type]] = {}

    @classmethod
    def register_core(cls, name: str, module_class: type) -> None:
        """Registreer een core module (beschikbaar voor alle tenants).

        Args:
            name: Unieke module naam.
            module_class: De module class.
        """
        cls._core_modules[name] = module_class

    @classmethod
    def register_tenant(
        cls, tenant: str, name: str, module_class: type
    ) -> None:
        """Registreer een tenant-specifieke module.

        Args:
            tenant: Tenant identifier.
            name: Module naam (mag overlappen met core).
            module_class: De module class.
        """
        if tenant not in cls._tenant_modules:
            cls._tenant_modules[tenant] = {}
        cls._tenant_modules[tenant][name] = module_class

    @classmethod
    def get(cls, name: str, tenant: str | None = None) -> type:
        """Zoek een module: eerst tenant-specifiek, dan core.

        Args:
            name: Module naam.
            tenant: Optionele tenant identifier.

        Returns:
            De gevonden module class.

        Raises:
            KeyError: Als de module niet gevonden is.
        """
        if tenant and tenant in cls._tenant_modules:
            if name in cls._tenant_modules[tenant]:
                return cls._tenant_modules[tenant][name]
        if name in cls._core_modules:
            return cls._core_modules[name]
        suffix = f" voor tenant {tenant}" if tenant else ""
        raise KeyError(f"Module '{name}' niet gevonden{suffix}")

    @classmethod
    def available(cls, tenant: str | None = None) -> list[str]:
        """Geef alle beschikbare module namen terug.

        Args:
            tenant: Optionele tenant — voegt tenant modules toe aan de lijst.

        Returns:
            Lijst van beschikbare module namen (core + eventueel tenant).
        """
        modules = list(cls._core_modules.keys())
        if tenant and tenant in cls._tenant_modules:
            modules.extend(cls._tenant_modules[tenant].keys())
        return modules

    @classmethod
    def has(cls, name: str, tenant: str | None = None) -> bool:
        """Check of een module geregistreerd is.

        Args:
            name: Module naam.
            tenant: Optionele tenant identifier.

        Returns:
            True als de module gevonden is.
        """
        if tenant and tenant in cls._tenant_modules:
            if name in cls._tenant_modules[tenant]:
                return True
        return name in cls._core_modules

    @classmethod
    def reset(cls) -> None:
        """Reset de registry (voor tests)."""
        cls._core_modules.clear()
        cls._tenant_modules.clear()


__all__ = ["ContentModule", "ModuleConfig", "ModuleRegistry"]
