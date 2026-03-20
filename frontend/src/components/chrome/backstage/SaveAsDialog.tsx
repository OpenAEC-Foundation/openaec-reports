import { useTranslation } from "react-i18next";

interface SaveAsDialogProps {
  open: boolean;
  onClose: () => void;
  onSaveServer: () => void;
  onSaveLocal: () => void;
}

export function SaveAsDialog({ open, onClose, onSaveServer, onSaveLocal }: SaveAsDialogProps) {
  const { t } = useTranslation("backstage");

  if (!open) return null;

  return (
    <div className="saveas-overlay" onClick={onClose}>
      <div className="saveas-dialog" onClick={(e) => e.stopPropagation()}>
        <h2 className="saveas-title">{t("saveAs")}</h2>
        <div className="saveas-options">
          <button
            className="saveas-card"
            onClick={() => { onSaveServer(); onClose(); }}
          >
            <span className="saveas-card-icon" dangerouslySetInnerHTML={{ __html: ICONS.server }} />
            <div className="saveas-card-text">
              <span className="saveas-card-label">{t("saveAsDialog.server")}</span>
              <span className="saveas-card-desc">{t("saveAsDialog.serverDesc")}</span>
            </div>
          </button>
          <button
            className="saveas-card"
            onClick={() => { onSaveLocal(); onClose(); }}
          >
            <span className="saveas-card-icon" dangerouslySetInnerHTML={{ __html: ICONS.local }} />
            <div className="saveas-card-text">
              <span className="saveas-card-label">{t("saveAsDialog.local")}</span>
              <span className="saveas-card-desc">{t("saveAsDialog.localDesc")}</span>
            </div>
          </button>
        </div>
      </div>
    </div>
  );
}

const ICONS = {
  server: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="2" width="20" height="8" rx="2" ry="2"/><rect x="2" y="14" width="20" height="8" rx="2" ry="2"/><line x1="6" y1="6" x2="6.01" y2="6"/><line x1="6" y1="18" x2="6.01" y2="18"/></svg>',
  local: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>',
};
