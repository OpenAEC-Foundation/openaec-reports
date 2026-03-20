import { useTranslation } from "react-i18next";

interface OpenDialogProps {
  open: boolean;
  onClose: () => void;
  onOpenServer: () => void;
  onOpenLocal: () => void;
}

export function OpenDialog({ open, onClose, onOpenServer, onOpenLocal }: OpenDialogProps) {
  const { t } = useTranslation("backstage");

  if (!open) return null;

  return (
    <div className="saveas-overlay" onClick={onClose}>
      <div className="saveas-dialog" onClick={(e) => e.stopPropagation()}>
        <h2 className="saveas-title">{t("open")}</h2>
        <div className="saveas-options">
          <button
            className="saveas-card"
            onClick={() => { onOpenServer(); onClose(); }}
          >
            <span className="saveas-card-icon" dangerouslySetInnerHTML={{ __html: ICONS.server }} />
            <div className="saveas-card-text">
              <span className="saveas-card-label">{t("openDialog.server")}</span>
              <span className="saveas-card-desc">{t("openDialog.serverDesc")}</span>
            </div>
          </button>
          <button
            className="saveas-card"
            onClick={() => { onOpenLocal(); onClose(); }}
          >
            <span className="saveas-card-icon" dangerouslySetInnerHTML={{ __html: ICONS.file }} />
            <div className="saveas-card-text">
              <span className="saveas-card-label">{t("openDialog.local")}</span>
              <span className="saveas-card-desc">{t("openDialog.localDesc")}</span>
            </div>
          </button>
        </div>
      </div>
    </div>
  );
}

const ICONS = {
  server: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="2" width="20" height="8" rx="2" ry="2"/><rect x="2" y="14" width="20" height="8" rx="2" ry="2"/><line x1="6" y1="6" x2="6.01" y2="6"/><line x1="6" y1="18" x2="6.01" y2="18"/></svg>',
  file: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><path d="M14 2v6h6"/><path d="M10 13l-2 2 2 2"/><path d="M14 13l2 2-2 2"/></svg>',
};
