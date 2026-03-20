import { useState, useEffect, useCallback, useRef } from "react";
import { useTranslation } from "react-i18next";
import { useReportStore } from "@/stores/reportStore";
import { useAuthStore } from "@/stores/authStore";
import "./Backstage.css";

const ICONS = {
  new: '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><path d="M14 2v6h6"/><path d="M12 18v-6m-3 3h6"/></svg>',
  open: '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 19a2 2 0 01-2 2H4a2 2 0 01-2-2V5a2 2 0 012-2h5l2 3h9a2 2 0 012 2z"/></svg>',
  save: '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17 3H5a2 2 0 00-2 2v14a2 2 0 002 2h14a2 2 0 002-2V7l-4-4z"/><path d="M17 3v4a1 1 0 01-1 1H8"/><path d="M7 14h10v7H7z"/></svg>',
  import: '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>',
  export: '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>',
  projects: '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M2 3h6a4 4 0 014 4v14a3 3 0 00-3-3H2z"/><path d="M22 3h-6a4 4 0 00-4 4v14a3 3 0 013-3h7z"/></svg>',
  preferences: '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 00.33 1.82l.06.06a2 2 0 010 2.83 2 2 0 01-2.83 0l-.06-.06a1.65 1.65 0 00-1.82-.33 1.65 1.65 0 00-1 1.51V21a2 2 0 01-4 0v-.09A1.65 1.65 0 009 19.4a1.65 1.65 0 00-1.82.33l-.06.06a2 2 0 01-2.83-2.83l.06-.06A1.65 1.65 0 004.68 15a1.65 1.65 0 00-1.51-1H3a2 2 0 010-4h.09A1.65 1.65 0 004.6 9a1.65 1.65 0 00-.33-1.82l-.06-.06a2 2 0 012.83-2.83l.06.06A1.65 1.65 0 009 4.68a1.65 1.65 0 001-1.51V3a2 2 0 014 0v.09a1.65 1.65 0 001 1.51 1.65 1.65 0 001.82-.33l.06-.06a2 2 0 012.83 2.83l-.06.06A1.65 1.65 0 0019.4 9a1.65 1.65 0 001.51 1H21a2 2 0 010 4h-.09a1.65 1.65 0 00-1.51 1z"/></svg>',
  account: '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 21v-2a4 4 0 00-4-4H8a4 4 0 00-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>',
  about: '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>',
  logout: '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9 21H5a2 2 0 01-2-2V5a2 2 0 012-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/></svg>',
};

function MenuItem({
  icon,
  label,
  shortcut,
  active,
  onClick,
}: {
  icon: string;
  label: string;
  shortcut?: string;
  active?: boolean;
  onClick: () => void;
}) {
  return (
    <button className={`backstage-item${active ? " active" : ""}`} onClick={onClick}>
      <span className="backstage-item-icon" dangerouslySetInnerHTML={{ __html: icon }} />
      <span className="backstage-item-label">{label}</span>
      {shortcut && <span className="backstage-item-shortcut">{shortcut}</span>}
    </button>
  );
}

function Divider() {
  return <div className="backstage-divider" />;
}

interface BackstageProps {
  open: boolean;
  onClose: () => void;
  onOpenSettings: () => void;
  onSave: () => void;
  onImport: () => void;
  onExport: () => void;
  onOpenProjects: () => void;
}

export default function Backstage({
  open,
  onClose,
  onOpenSettings,
  onSave,
  onImport,
  onExport,
  onOpenProjects,
}: BackstageProps) {
  const { t } = useTranslation("backstage");
  const [activePanel, setActivePanel] = useState<string>("none");
  const isDirty = useReportStore((s) => s.isDirty);
  const reset = useReportStore((s) => s.reset);
  const authUser = useAuthStore((s) => s.user);
  const logout = useAuthStore((s) => s.logout);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const actionAndClose = useCallback(
    (fn?: () => void) => {
      onClose();
      fn?.();
    },
    [onClose],
  );

  useEffect(() => {
    if (!open) {
      setActivePanel("none");
      return;
    }
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [open, onClose]);

  if (!open) return null;

  const handleNew = () => {
    if (isDirty) {
      if (!confirm("Huidig rapport verwijderen? Onopgeslagen wijzigingen gaan verloren.")) return;
    }
    reset();
    onClose();
  };

  const handleContentClick = (e: React.MouseEvent) => {
    if (e.target === e.currentTarget) onClose();
  };

  return (
    <div className="backstage-overlay">
      <input
        ref={fileInputRef}
        type="file"
        accept=".json"
        className="hidden"
        style={{ display: "none" }}
        onChange={(e) => {
          const file = e.target.files?.[0];
          if (!file) return;
          const reader = new FileReader();
          reader.onload = () => {
            onImport();
            onClose();
          };
          reader.readAsText(file);
          e.target.value = "";
        }}
      />
      <div className="backstage-sidebar">
        <button className="backstage-back" onClick={onClose}>
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M19 12H5M12 19l-7-7 7-7" />
          </svg>
          <span>{t("file")}</span>
        </button>
        <div className="backstage-items">
          <MenuItem icon={ICONS.new} label={t("new")} shortcut="Ctrl+N" onClick={handleNew} />
          <MenuItem icon={ICONS.open} label={t("open")} onClick={() => actionAndClose(onOpenProjects)} />
          <MenuItem icon={ICONS.save} label={t("save")} shortcut="Ctrl+S" onClick={() => actionAndClose(onSave)} />
          <Divider />
          <MenuItem icon={ICONS.import} label={t("import")} onClick={() => actionAndClose(onImport)} />
          <MenuItem icon={ICONS.export} label={t("export")} onClick={() => actionAndClose(onExport)} />
          <Divider />
          <MenuItem icon={ICONS.projects} label={t("projects")} onClick={() => actionAndClose(onOpenProjects)} />
          <MenuItem icon={ICONS.preferences} label={t("preferences")} shortcut="Ctrl+," onClick={() => actionAndClose(onOpenSettings)} />
          <Divider />
          <MenuItem
            icon={ICONS.about}
            label={t("about")}
            active={activePanel === "about"}
            onClick={() => setActivePanel("about")}
          />
          {authUser && (
            <>
              <Divider />
              <MenuItem
                icon={ICONS.account}
                label={authUser.display_name || authUser.username}
                active={activePanel === "account"}
                onClick={() => setActivePanel("account")}
              />
              <MenuItem icon={ICONS.logout} label={t("logout")} onClick={() => actionAndClose(logout)} />
            </>
          )}
        </div>
      </div>
      <div className="backstage-content" onClick={handleContentClick}>
        {activePanel === "about" && <AboutPanel />}
        {activePanel === "account" && authUser && <AccountPanel />}
      </div>
    </div>
  );
}

function AboutPanel() {
  const { t } = useTranslation("backstage");
  return (
    <div className="bs-about-panel">
      <h2 className="bs-about-title">{t("aboutPanel.title")}</h2>
      <div className="bs-about-app">
        <div className="bs-about-logo">
          <svg viewBox="0 0 1024 1024" fill="none" xmlns="http://www.w3.org/2000/svg">
            <rect x="40" y="40" width="944" height="944" rx="180" fill="var(--theme-accent)" />
            <text x="512" y="580" textAnchor="middle" dominantBaseline="middle" fill="var(--theme-accent-text)" fontSize="280" fontFamily="Arial, sans-serif" fontWeight="600">
              OA
            </text>
          </svg>
        </div>
        <div className="bs-about-app-info">
          <h1 className="bs-about-app-name">{t("aboutPanel.appName")}</h1>
          <p className="bs-about-version">{t("aboutPanel.version")} 0.1.0</p>
        </div>
      </div>
      <p className="bs-about-tagline">{t("aboutPanel.tagline")}</p>
      <p className="bs-about-description">{t("aboutPanel.description")}</p>
      <div className="bs-about-company">
        <h3 className="bs-about-company-name">{t("aboutPanel.companyName")}</h3>
        <p className="bs-about-company-desc">{t("aboutPanel.companyDescription")}</p>
      </div>
    </div>
  );
}

function AccountPanel() {
  const authUser = useAuthStore((s) => s.user);
  if (!authUser) return null;

  return (
    <div className="bs-about-panel">
      <h2 className="bs-about-title">Account</h2>
      <div style={{ fontSize: 12, lineHeight: 1.8 }}>
        <p><strong>Gebruiker:</strong> {authUser.display_name || authUser.username}</p>
        <p><strong>Rol:</strong> {authUser.role}</p>
        {authUser.tenant && <p><strong>Tenant:</strong> {authUser.tenant}</p>}
      </div>
    </div>
  );
}
