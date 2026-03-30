import { useState } from "react";
import { useAdminStore } from "@/stores/adminStore";

export function TenantManagement() {
  const tenants = useAdminStore((s) => s.tenants);
  const tenantsLoading = useAdminStore((s) => s.tenantsLoading);
  const createTenant = useAdminStore((s) => s.createTenant);
  const deleteTenant = useAdminStore((s) => s.deleteTenant);
  const selectTenant = useAdminStore((s) => s.selectTenant);
  const setActiveTab = useAdminStore((s) => s.setActiveTab);

  const [showForm, setShowForm] = useState(false);
  const [newName, setNewName] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [creating, setCreating] = useState(false);

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    if (!newName.trim()) return;

    setCreating(true);
    const tenant = await createTenant({
      name: newName.trim(),
      display_name: displayName.trim() || undefined,
    });
    setCreating(false);

    if (tenant) {
      setNewName("");
      setDisplayName("");
      setShowForm(false);
      // Navigeer naar Brand tab met de nieuwe tenant geselecteerd
      selectTenant(tenant.name);
      setActiveTab("brand");
    }
  }

  async function handleDelete(name: string) {
    if (!confirm(`Tenant '${name}' en ALLE bijbehorende bestanden verwijderen? Dit kan niet ongedaan worden.`)) {
      return;
    }
    await deleteTenant(name);
  }

  function handleManage(name: string) {
    selectTenant(name);
    setActiveTab("brand");
  }

  if (tenantsLoading) {
    return (
      <div className="flex items-center gap-2 text-sm text-oaec-text-muted py-8">
        <svg className="h-4 w-4 animate-spin" fill="none" viewBox="0 0 24 24">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
        </svg>
        Tenants laden...
      </div>
    );
  }

  return (
    <div>
      {/* Header met "Nieuwe tenant" knop */}
      <div className="flex items-center justify-between mb-6">
        <p className="text-sm text-oaec-text-muted">
          {tenants.length} tenant{tenants.length !== 1 ? "s" : ""} geconfigureerd
        </p>
        <button
          onClick={() => setShowForm(!showForm)}
          className="rounded-md bg-oaec-accent px-4 py-2 text-sm font-medium text-oaec-accent-text hover:bg-oaec-accent-hover transition-colors"
        >
          {showForm ? "Annuleren" : "Nieuwe tenant"}
        </button>
      </div>

      {/* Inline create form */}
      {showForm && (
        <form
          onSubmit={handleCreate}
          className="mb-6 rounded-lg border border-oaec-border bg-oaec-accent-soft p-4"
        >
          <h3 className="text-sm font-semibold text-oaec-text-secondary mb-3">Nieuwe tenant aanmaken</h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-4">
            <div>
              <label className="block text-xs font-medium text-oaec-text-secondary mb-1">
                Naam (slug) *
              </label>
              <input
                type="text"
                value={newName}
                onChange={(e) => setNewName(e.target.value)}
                placeholder="bijv. mijn_bedrijf"
                pattern="^[\w\-]+$"
                required
                className="w-full rounded-md border border-oaec-border px-3 py-1.5 text-sm shadow-sm focus:border-oaec-accent focus:ring-1 focus:ring-oaec-accent"
              />
              <p className="mt-1 text-xs text-oaec-text-faint">
                Alleen letters, cijfers, underscores en streepjes
              </p>
            </div>
            <div>
              <label className="block text-xs font-medium text-oaec-text-secondary mb-1">
                Weergavenaam
              </label>
              <input
                type="text"
                value={displayName}
                onChange={(e) => setDisplayName(e.target.value)}
                placeholder="bijv. Mijn Bedrijf B.V."
                className="w-full rounded-md border border-oaec-border px-3 py-1.5 text-sm shadow-sm focus:border-oaec-accent focus:ring-1 focus:ring-oaec-accent"
              />
            </div>
          </div>
          <button
            type="submit"
            disabled={creating || !newName.trim()}
            className="rounded-md bg-oaec-accent px-4 py-2 text-sm font-medium text-oaec-accent-text hover:bg-oaec-accent-hover disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {creating ? "Aanmaken..." : "Aanmaken"}
          </button>
        </form>
      )}

      {/* Tenant overzicht */}
      {tenants.length === 0 ? (
        <div className="text-center py-12">
          <p className="text-sm text-oaec-text-muted mb-2">Nog geen tenants aangemaakt</p>
          <p className="text-xs text-oaec-text-faint">
            Maak een tenant aan om brand configuratie, templates en assets te beheren
          </p>
        </div>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {tenants.map((tenant) => (
            <div
              key={tenant.name}
              className="rounded-lg border border-oaec-border bg-oaec-bg-lighter p-4 hover:shadow-sm transition-shadow"
            >
              <div className="flex items-start justify-between mb-3">
                <h3 className="text-sm font-semibold text-oaec-text">{tenant.name}</h3>
                {tenant.has_brand && (
                  <span className="shrink-0 rounded-full bg-oaec-success-soft px-2 py-0.5 text-xs font-medium text-oaec-success">
                    Brand
                  </span>
                )}
              </div>

              {/* Status indicators */}
              <div className="grid grid-cols-2 gap-x-4 gap-y-1 text-xs text-oaec-text-muted mb-4">
                <div className="flex justify-between">
                  <span>Templates</span>
                  <span className="font-medium text-oaec-text-secondary">{tenant.template_count}</span>
                </div>
                <div className="flex justify-between">
                  <span>Stationery</span>
                  <span className="font-medium text-oaec-text-secondary">{tenant.stationery_count}</span>
                </div>
                <div className="flex justify-between">
                  <span>Logo's</span>
                  <span className="font-medium text-oaec-text-secondary">{tenant.logo_count}</span>
                </div>
                <div className="flex justify-between">
                  <span>Fonts</span>
                  <span className="font-medium text-oaec-text-secondary">{tenant.font_count}</span>
                </div>
              </div>

              {/* Actions */}
              <div className="flex items-center gap-2 pt-3 border-t border-oaec-border-subtle">
                <button
                  onClick={() => handleManage(tenant.name)}
                  className="flex-1 rounded-md bg-oaec-hover px-3 py-1.5 text-xs font-medium text-oaec-text-secondary hover:bg-oaec-hover-strong transition-colors"
                >
                  Beheren
                </button>
                <button
                  onClick={() => handleDelete(tenant.name)}
                  className="rounded-md px-3 py-1.5 text-xs font-medium text-oaec-danger hover:bg-oaec-danger-soft hover:text-oaec-danger transition-colors"
                >
                  Verwijderen
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
