import { useEffect } from "react";
import { useAdminStore } from "@/stores/adminStore";
import { TenantManagement } from "./TenantManagement";
import { UserManagement } from "./UserManagement";
import { TemplateManagement } from "./TemplateManagement";
import { BrandManagement } from "./BrandManagement";
import { HelpPanel } from "./HelpPanel";

const TABS = [
  { key: "tenants" as const, label: "Tenants" },
  { key: "users" as const, label: "Gebruikers" },
  { key: "templates" as const, label: "Templates" },
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
        <h1 className="text-2xl font-bold text-gray-900">Beheer</h1>
        <p className="text-sm text-gray-500 mt-1">
          Tenants, gebruikers, templates en brand configuratie beheren
        </p>
      </div>

      {/* Error banner */}
      {error && (
        <div className="mb-4 flex items-center justify-between rounded-lg bg-red-50 border border-red-200 px-4 py-3">
          <span className="text-sm text-red-700">{error}</span>
          <button
            onClick={clearError}
            className="text-red-500 hover:text-red-700 text-sm font-medium"
          >
            Sluiten
          </button>
        </div>
      )}

      {/* Sub-tabs */}
      <div className="border-b border-gray-200 mb-6">
        <nav className="flex gap-6">
          {TABS.map((tab) => (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key)}
              className={`pb-3 text-sm font-medium border-b-2 transition-colors ${
                activeTab === tab.key
                  ? "border-purple-600 text-purple-600"
                  : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
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
      {activeTab === "templates" && <TemplateManagement />}
      {activeTab === "brand" && <BrandManagement />}
      {activeTab === "help" && <HelpPanel />}
    </div>
  );
}
