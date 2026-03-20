import { useState, useRef, useEffect } from "react";
import { useTranslation } from "react-i18next";
import { useReportStore } from "@/stores/reportStore";
import { useAuthStore } from "@/stores/authStore";
import { getAuthentikUserUrl } from "@/config/oidc";
import "./TitleBar.css";

interface TitleBarProps {
  onSave: () => void;
  onSettingsClick?: () => void;
  onHelpClick?: () => void;
  onAdmin?: () => void;
  isSaving?: boolean;
}

export default function TitleBar({ onSave, onSettingsClick, onHelpClick, onAdmin, isSaving }: TitleBarProps) {
  const { t } = useTranslation();
  const canUndo = useReportStore((s) => s.canUndo);
  const canRedo = useReportStore((s) => s.canRedo);
  const undo = useReportStore((s) => s.undo);
  const redo = useReportStore((s) => s.redo);
  const isDirty = useReportStore((s) => s.isDirty);
  const authUser = useAuthStore((s) => s.user);
  const logout = useAuthStore((s) => s.logout);

  const [menuOpen, setMenuOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);

  const initials = authUser
    ? (authUser.display_name || authUser.username)
        .split(" ")
        .map((w) => w[0])
        .slice(0, 2)
        .join("")
        .toUpperCase()
    : "";

  const authentikUrl = getAuthentikUserUrl();

  // Close dropdown on outside click
  useEffect(() => {
    if (!menuOpen) return;
    const handleClick = (e: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setMenuOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, [menuOpen]);

  return (
    <div className="titlebar">
      <div className="titlebar-left">
        <div className="titlebar-icon">
          <svg
            width="16"
            height="16"
            viewBox="0 0 1024 1024"
            fill="none"
            xmlns="http://www.w3.org/2000/svg"
          >
            <rect x="40" y="40" width="944" height="944" rx="180" fill="var(--theme-accent)" />
            <text
              x="512"
              y="580"
              textAnchor="middle"
              dominantBaseline="middle"
              fill="var(--theme-accent-text)"
              fontSize="280"
              fontFamily="Arial, sans-serif"
              fontWeight="600"
            >
              OA
            </text>
          </svg>
        </div>

        <div className="titlebar-quick-access">
          <button
            className="titlebar-quick-btn"
            title={`${t("save")} (Ctrl+S)`}
            aria-label={t("save")}
            tabIndex={-1}
            onClick={onSave}
            disabled={isSaving}
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M19 21H5a2 2 0 01-2-2V5a2 2 0 012-2h11l5 5v11a2 2 0 01-2 2z" />
              <polyline points="17 21 17 13 7 13 7 21" />
              <polyline points="7 3 7 8 15 8" />
            </svg>
          </button>
          <button
            className="titlebar-quick-btn"
            title={`${t("undo")} (Ctrl+Z)`}
            aria-label={t("undo")}
            tabIndex={-1}
            onClick={undo}
            disabled={!canUndo}
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <polyline points="1 4 1 10 7 10" />
              <path d="M3.51 15a9 9 0 102.13-9.36L1 10" />
            </svg>
          </button>
          <button
            className="titlebar-quick-btn"
            title={`${t("redo")} (Ctrl+Y)`}
            aria-label={t("redo")}
            tabIndex={-1}
            onClick={redo}
            disabled={!canRedo}
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <polyline points="23 4 23 10 17 10" />
              <path d="M20.49 15a9 9 0 11-2.13-9.36L23 10" />
            </svg>
          </button>
          <button
            className="titlebar-quick-btn"
            title={t("preferences")}
            aria-label={t("preferences")}
            tabIndex={-1}
            onClick={onSettingsClick}
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <circle cx="12" cy="12" r="3" />
              <path d="M19.4 15a1.65 1.65 0 00.33 1.82l.06.06a2 2 0 010 2.83 2 2 0 01-2.83 0l-.06-.06a1.65 1.65 0 00-1.82-.33 1.65 1.65 0 00-1 1.51V21a2 2 0 01-4 0v-.09A1.65 1.65 0 009 19.4a1.65 1.65 0 00-1.82.33l-.06.06a2 2 0 01-2.83-2.83l.06-.06A1.65 1.65 0 004.68 15a1.65 1.65 0 00-1.51-1H3a2 2 0 010-4h.09A1.65 1.65 0 004.6 9a1.65 1.65 0 00-.33-1.82l-.06-.06a2 2 0 012.83-2.83l.06.06A1.65 1.65 0 009 4.68a1.65 1.65 0 001-1.51V3a2 2 0 014 0v.09a1.65 1.65 0 001 1.51 1.65 1.65 0 001.82-.33l.06-.06a2 2 0 012.83 2.83l-.06.06A1.65 1.65 0 0019.4 9a1.65 1.65 0 001.51 1H21a2 2 0 010 4h-.09a1.65 1.65 0 00-1.51 1z" />
            </svg>
          </button>
          <button
            className="titlebar-quick-btn"
            title="Help (?)"
            aria-label="Help"
            tabIndex={-1}
            onClick={onHelpClick}
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </button>
        </div>
      </div>

      <span className="titlebar-title">
        {t("appName")}
        {isDirty && <span className="titlebar-dirty"> *</span>}
      </span>

      <div className="titlebar-controls">
        {authUser && (
          <div className="titlebar-user" ref={menuRef}>
            <button
              className="titlebar-user-trigger"
              onClick={() => setMenuOpen((v) => !v)}
              title={authUser.display_name || authUser.username}
            >
              <div className="titlebar-avatar">
                {initials}
              </div>
              <span className="titlebar-username">{authUser.display_name || authUser.username}</span>
              <svg className="titlebar-chevron" width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <polyline points="6 9 12 15 18 9" />
              </svg>
            </button>
            {menuOpen && (
              <div className="titlebar-user-menu">
                {authentikUrl && (
                  <>
                    <a
                      className="titlebar-menu-item"
                      href={authentikUrl}
                      target="_blank"
                      rel="noopener noreferrer"
                      onClick={() => setMenuOpen(false)}
                    >
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                        <path d="M20 21v-2a4 4 0 00-4-4H8a4 4 0 00-4 4v2" />
                        <circle cx="12" cy="7" r="4" />
                      </svg>
                      <span>{t("myAccount")}</span>
                      <svg className="titlebar-menu-external" width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                        <path d="M18 13v6a2 2 0 01-2 2H5a2 2 0 01-2-2V8a2 2 0 012-2h6" />
                        <polyline points="15 3 21 3 21 9" />
                        <line x1="10" y1="14" x2="21" y2="3" />
                      </svg>
                    </a>
                    <a
                      className="titlebar-menu-item"
                      href={`${authentikUrl}#/settings`}
                      target="_blank"
                      rel="noopener noreferrer"
                      onClick={() => setMenuOpen(false)}
                    >
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                        <circle cx="12" cy="12" r="3" />
                        <path d="M19.4 15a1.65 1.65 0 00.33 1.82l.06.06a2 2 0 010 2.83 2 2 0 01-2.83 0l-.06-.06a1.65 1.65 0 00-1.82-.33 1.65 1.65 0 00-1 1.51V21a2 2 0 01-4 0v-.09A1.65 1.65 0 009 19.4a1.65 1.65 0 00-1.82.33l-.06.06a2 2 0 01-2.83-2.83l.06-.06A1.65 1.65 0 004.68 15a1.65 1.65 0 00-1.51-1H3a2 2 0 010-4h.09A1.65 1.65 0 004.6 9a1.65 1.65 0 00-.33-1.82l-.06-.06a2 2 0 012.83-2.83l.06.06A1.65 1.65 0 009 4.68a1.65 1.65 0 001-1.51V3a2 2 0 014 0v.09a1.65 1.65 0 001 1.51 1.65 1.65 0 001.82-.33l.06-.06a2 2 0 012.83 2.83l-.06.06A1.65 1.65 0 0019.4 9a1.65 1.65 0 001.51 1H21a2 2 0 010 4h-.09a1.65 1.65 0 00-1.51 1z" />
                      </svg>
                      <span>{t("ssoSettings")}</span>
                      <svg className="titlebar-menu-external" width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                        <path d="M18 13v6a2 2 0 01-2 2H5a2 2 0 01-2-2V8a2 2 0 012-2h6" />
                        <polyline points="15 3 21 3 21 9" />
                        <line x1="10" y1="14" x2="21" y2="3" />
                      </svg>
                    </a>
                  </>
                )}
                {authUser.role === "admin" && onAdmin && (
                  <button
                    className="titlebar-menu-item"
                    onClick={() => { setMenuOpen(false); onAdmin(); }}
                  >
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <path d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                    </svg>
                    <span>{t("view.admin", { ns: "ribbon" })}</span>
                  </button>
                )}
                <button
                  className="titlebar-menu-item"
                  onClick={() => { setMenuOpen(false); logout(); }}
                >
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M9 21H5a2 2 0 01-2-2V5a2 2 0 012-2h4" />
                    <polyline points="16 17 21 12 16 7" />
                    <line x1="21" y1="12" x2="9" y2="12" />
                  </svg>
                  <span>{t("logout")}</span>
                </button>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
