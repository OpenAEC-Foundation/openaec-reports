import { useTranslation } from "react-i18next";
import { useReportStore } from "@/stores/reportStore";
import { useApiStore } from "@/stores/apiStore";
import "./StatusBar.css";

export default function StatusBar() {
  const { t } = useTranslation();
  const sections = useReportStore((s) => s.report.sections);
  const appendices = useReportStore((s) => s.report.appendices);
  const connected = useApiStore((s) => s.connected);
  const checking = useApiStore((s) => s.checking);
  const backendVersion = useApiStore((s) => s.backendVersion);

  const totalBlocks =
    sections.reduce((sum, s) => sum + s.content.length, 0) +
    appendices.reduce((sum, a) => sum + a.content.length, 0);

  return (
    <div className="status-bar">
      <div className="status-bar-left">
        <div className="status-item">
          <span className="status-item-label">{t("ready")}</span>
        </div>
        <div className="status-separator" />
        <div className="status-item">
          <span className="status-item-value">
            {sections.length} {t("chapters")}
          </span>
        </div>
        {appendices.length > 0 && (
          <>
            <div className="status-separator" />
            <div className="status-item">
              <span className="status-item-value">
                {appendices.length} {t("appendices")}
              </span>
            </div>
          </>
        )}
        <div className="status-separator" />
        <div className="status-item">
          <span className="status-item-value">
            {totalBlocks} {t("blocks")}
          </span>
        </div>
      </div>

      <div className="status-bar-center" />

      <div className="status-bar-right">
        <div className="status-item">
          <span
            className="status-indicator"
            data-state={checking ? "checking" : connected ? "connected" : "offline"}
          />
          <span className="status-item-value">
            {checking
              ? t("connecting")
              : connected
                ? `v${backendVersion}`
                : t("offline")}
          </span>
        </div>
      </div>
    </div>
  );
}
