import { useTranslation } from "react-i18next";
import { useReportStore } from "@/stores/reportStore";
import RibbonGroup from "./RibbonGroup";
import RibbonButton from "./RibbonButton";
import {
  newSectionIcon,
  newAppendixIcon,
  paragraphIcon,
  calculationIcon,
  checkIcon,
  tableIcon,
  imageIcon,
  mapIcon,
  bulletListIcon,
  heading2Icon,
} from "./icons";

export default function InsertTab() {
  const { t } = useTranslation("ribbon");
  const addNewSection = useReportStore((s) => s.addNewSection);
  const addNewAppendix = useReportStore((s) => s.addNewAppendix);

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
        <RibbonGroup label={t("insert.sections")}>
          <RibbonButton icon={newSectionIcon} label={t("insert.newSection")} onClick={() => addNewSection()} />
          <RibbonButton icon={newAppendixIcon} label={t("insert.newAppendix")} onClick={() => addNewAppendix()} />
        </RibbonGroup>

        <RibbonGroup label={t("insert.content")}>
          <RibbonButton icon={paragraphIcon} label={t("home.paragraph")} onClick={() => addBlock("paragraph")} />
          <RibbonButton icon={calculationIcon} label={t("home.calculation")} onClick={() => addBlock("calculation")} />
          <RibbonButton icon={checkIcon} label={t("home.check")} onClick={() => addBlock("check")} />
          <RibbonButton icon={tableIcon} label={t("home.table")} onClick={() => addBlock("table")} />
          <RibbonButton icon={imageIcon} label={t("home.image")} onClick={() => addBlock("image")} />
          <RibbonButton icon={mapIcon} label={t("home.map")} onClick={() => addBlock("map")} />
          <RibbonButton icon={bulletListIcon} label={t("home.bulletList")} onClick={() => addBlock("bullet_list")} />
          <RibbonButton icon={heading2Icon} label={t("home.heading2")} onClick={() => addBlock("heading_2")} />
        </RibbonGroup>
      </div>
    </div>
  );
}
