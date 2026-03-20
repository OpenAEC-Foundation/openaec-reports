import { useTranslation } from "react-i18next";
import { useReportStore } from "@/stores/reportStore";
import "./TitleBar.css";

interface TitleBarProps {
  onSave: () => void;
  onSettingsClick?: () => void;
  onHelpClick?: () => void;
  isSaving?: boolean;
}

export default function TitleBar({ onSave, onSettingsClick, onHelpClick, isSaving }: TitleBarProps) {
  const { t } = useTranslation();
  const canUndo = useReportStore((s) => s.canUndo);
  const canRedo = useReportStore((s) => s.canRedo);
  const undo = useReportStore((s) => s.undo);
  const redo = useReportStore((s) => s.redo);
  const isDirty = useReportStore((s) => s.isDirty);

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

      <div className="titlebar-controls" />
    </div>
  );
}
