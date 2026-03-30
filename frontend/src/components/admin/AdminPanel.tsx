import { useEffect } from "react";
import { useAdminStore } from "@/stores/adminStore";
import { TenantManagement } from "./TenantManagement";
import { UserManagement } from "./UserManagement";
import { ApiKeyManagement } from "./ApiKeyManagement";
import { TemplateManagement } from "./TemplateManagement";
import { BrandManagement } from "./BrandManagement";

import { HelpPanel } from "./HelpPanel";

const TABS = [
  { key: "tenants" as const, label: "Tenants" },
  { key: "users" as const, label: "Gebruikers" },

  { key: "api-keys" as const, label: "API Keys" },
  { key: "templates" as const, label: "YAML Bestanden" },
  { key: "brand" as const, label: "Brand" },
  { key: "help" as const, label: "📖 Help" },
];

export function AdminPanel() {
  const activeTab = useAdminStore((s) => s.activeTab);
  const setActiveTab = useAdminStore((s) => s.setActiveTab);
  const error = useAdminStore((s) => s.error);
  const clearError = useAdminStore((s) => s.clearError);
  const loadUsers = useAdminStore((s) => s.loadUsers);
  const loadTenants = useAdminStore((s) => s.loadTenants);

  useEffect(() => {
    loadUsers();
    loadTenants();
  }, [loadUsers, loadTenants]);

  return (
    <div className="mx-auto max-w-6xl px-6 py-6">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-oaec-text">Beheer</h1>
        <p className="text-sm text-oaec-text-muted mt-1">
          Tenants, gebruikers, templates en brand configuratie beheren
        </p>
      </div>

      {/* Error banner */}
      {error && (
        <div className="mb-4 flex items-center justify-between rounded-lg bg-oaec-danger-soft border border-oaec-border px-4 py-3">
          <span className="text-sm text-oaec-danger">{error}</span>
          <button
            onClick={clearError}
            className="text-oaec-danger hover:text-oaec-danger text-sm font-medium"
          >
            Sluiten
          </button>
        </div>
      )}

      {/* Sub-tabs */}
      <div className="border-b border-oaec-border mb-6">
        <nav className="flex gap-6">
          {TABS.map((tab) => (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key)}
              className={`pb-3 text-sm font-medium border-b-2 transition-colors ${
                activeTab === tab.key
                  ? "border-oaec-accent text-oaec-accent"
                  : "border-transparent text-oaec-text-muted hover:text-oaec-text-secondary hover:border-oaec-border"
              }`}
            >
              {tab.label}
            </button>
          ))}
        </nav>
      </div>

      {/* Active panel */}
      {activeTab === "tenants" && <TenantManagement />}
      {activeTab === "users" && <UserManagement />}

      {activeTab === "api-keys" && <ApiKeyManagement />}
      {activeTab === "templates" && <TemplateManagement />}
      {activeTab === "brand" && <BrandManagement />}
      {activeTab === "help" && <HelpPanel />}
    </div>
  );
}
