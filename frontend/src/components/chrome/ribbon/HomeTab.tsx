import { useTranslation } from "react-i18next";
import { useReportStore } from "@/stores/reportStore";
import { useApiStore } from "@/stores/apiStore";
import RibbonGroup from "./RibbonGroup";
import RibbonButton from "./RibbonButton";
import RibbonButtonStack from "./RibbonButtonStack";
import {
  pasteIcon,
  copyIcon,
  paragraphIcon,
  calculationIcon,
  checkIcon,
  tableIcon,
  spreadsheetIcon,
  imageIcon,
  mapIcon,
  bulletListIcon,
  heading2Icon,
  spacerIcon,
  pageBreakIcon,
  validateIcon,
  generatePdfIcon,
  downloadIcon,
} from "./icons";

interface HomeTabProps {
  onValidate: () => void;
}

export default function HomeTab({ onValidate }: HomeTabProps) {
  const { t } = useTranslation("ribbon");
  const connected = useApiStore((s) => s.connected);
  const isValidating = useApiStore((s) => s.isValidating);
  const isGenerating = useApiStore((s) => s.isGenerating);
  const generatePdf = useApiStore((s) => s.generatePdf);
  const downloadPdf = useApiStore((s) => s.downloadPdf);
  const lastPdfUrl = useApiStore((s) => s.lastPdfUrl);

  const addBlock = (type: string) => {
    const state = useReportStore.getState();
    if (state.activeSection) {
      state.addNewBlock(state.activeSection, type as "paragraph");
    } else if (state.activeAppendix) {
      state.addNewAppendixBlock(state.activeAppendix, type as "paragraph");
    }
  };

  return (
    <div className="ribbon-content">
      <div className="ribbon-groups">
        <RibbonGroup label={t("home.clipboard")}>
          <RibbonButtonStack>
            <RibbonButton icon={pasteIcon} label={t("home.paste")} size="small" />
            <RibbonButton icon={copyIcon} label={t("home.copySection")} size="small" />
          </RibbonButtonStack>
        </RibbonGroup>

        <RibbonGroup label={t("home.blocks")}>
          <RibbonButton icon={paragraphIcon} label={t("home.paragraph")} onClick={() => addBlock("paragraph")} />
          <RibbonButton icon={calculationIcon} label={t("home.calculation")} onClick={() => addBlock("calculation")} />
          <RibbonButton icon={checkIcon} label={t("home.check")} onClick={() => addBlock("check")} />
          <RibbonButton icon={tableIcon} label={t("home.table")} onClick={() => addBlock("table")} />
          <RibbonButton icon={spreadsheetIcon} label={t("home.spreadsheet")} onClick={() => addBlock("spreadsheet")} />
          <RibbonButton icon={imageIcon} label={t("home.image")} onClick={() => addBlock("image")} />
          <RibbonButtonStack>
            <RibbonButton icon={mapIcon} label={t("home.map")} size="small" onClick={() => addBlock("map")} />
            <RibbonButton icon={bulletListIcon} label={t("home.bulletList")} size="small" onClick={() => addBlock("bullet_list")} />
            <RibbonButton icon={heading2Icon} label={t("home.heading2")} size="small" onClick={() => addBlock("heading_2")} />
          </RibbonButtonStack>
        </RibbonGroup>

        <RibbonGroup label={t("home.page")}>
          <RibbonButtonStack>
            <RibbonButton icon={spacerIcon} label={t("home.spacer")} size="small" onClick={() => addBlock("spacer")} />
            <RibbonButton icon={pageBreakIcon} label={t("home.pageBreak")} size="small" onClick={() => addBlock("page_break")} />
          </RibbonButtonStack>
        </RibbonGroup>

        <RibbonGroup label={t("home.control")}>
          <RibbonButton
            icon={validateIcon}
            label={t("home.validate")}
            onClick={onValidate}
            disabled={!connected || isValidating}
          />
        </RibbonGroup>

        <RibbonGroup label={t("home.output")}>
          <RibbonButton
            icon={generatePdfIcon}
            label={t("home.generatePdf")}
            onClick={generatePdf}
            disabled={!connected || isGenerating}
          />
          <RibbonButton
            icon={downloadIcon}
            label={t("home.downloadPdf")}
            onClick={downloadPdf}
            disabled={!lastPdfUrl}
          />
        </RibbonGroup>
      </div>
    </div>
  );
}
