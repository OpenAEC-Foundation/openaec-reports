import { useTranslation } from "react-i18next";
import { useReportStore } from "@/stores/reportStore";
import type { ViewMode } from "@/stores/reportStore";
import { useApiStore } from "@/stores/apiStore";
import RibbonGroup from "./RibbonGroup";
import RibbonButton from "./RibbonButton";
import { editorIcon, splitIcon, jsonIcon, previewIcon, sidebarIcon } from "./icons";

interface ViewTabProps {
  sidebarVisible: boolean;
  onToggleSidebar: () => void;
}

export default function ViewTab({ sidebarVisible, onToggleSidebar }: ViewTabProps) {
  const { t } = useTranslation("ribbon");
  const viewMode = useReportStore((s) => s.viewMode);
  const setViewMode = useReportStore((s) => s.setViewMode);

  const setMode = (mode: ViewMode) => {
    setViewMode(mode);
    // Auto-generate PDF wanneer user naar preview/split schakelt zonder bestaande preview
    if (mode === "split" || mode === "preview") {
      const { lastPdfUrl, connected, isGenerating, generatePdf } = useApiStore.getState();
      if (!lastPdfUrl && connected && !isGenerating) {
        generatePdf();
      }
    }
  };

  return (
    <div className="ribbon-content">
      <div className="ribbon-groups">
        <RibbonGroup label={t("view.display")}>
          <RibbonButton icon={editorIcon} label={t("view.editor")} active={viewMode === "editor"} onClick={() => setMode("editor")} />
          <RibbonButton icon={splitIcon} label={t("view.split")} active={viewMode === "split"} onClick={() => setMode("split")} />
          <RibbonButton icon={jsonIcon} label={t("view.json")} active={viewMode === "json"} onClick={() => setMode("json")} />
          <RibbonButton icon={previewIcon} label={t("view.previewView")} active={viewMode === "preview"} onClick={() => setMode("preview")} />
        </RibbonGroup>

        <RibbonGroup label={t("view.panels")}>
          <RibbonButton
            icon={sidebarIcon}
            label={t("view.sidebar")}
            active={sidebarVisible}
            onClick={onToggleSidebar}
          />
        </RibbonGroup>
      </div>
    </div>
  );
}
