import { useState, useEffect } from "react";
import { useTranslation } from "react-i18next";
import Modal from "../chrome/Modal";
import "./FeedbackDialog.css";

const GITHUB_REPO = "OpenAEC-Foundation/openaec-reports";
const GITHUB_NEW_ISSUE_URL = `https://github.com/${GITHUB_REPO}/issues/new`;

const CATEGORIES = ["bug", "feature", "general"] as const;
type Category = (typeof CATEGORIES)[number];

const CATEGORY_LABELS: Record<Category, string> = {
  bug: "bug",
  feature: "enhancement",
  general: "feedback",
};

const MIN_TITLE_CHARS = 5;
const MIN_DESC_CHARS = 10;
const MAX_DESC_CHARS = 5000;

interface FeedbackDialogProps {
  open: boolean;
  onClose: () => void;
}

export default function FeedbackDialog({ open, onClose }: FeedbackDialogProps) {
  const { t } = useTranslation("feedback");
  const { t: tCommon } = useTranslation("common");

  const [title, setTitle] = useState("");
  const [category, setCategory] = useState<Category>("bug");
  const [description, setDescription] = useState("");

  useEffect(() => {
    if (open) {
      setTitle("");
      setCategory("bug");
      setDescription("");
    }
  }, [open]);

  const handleSubmit = () => {
    const trimmedTitle = title.trim();
    const trimmedDesc = description.trim();
    if (trimmedTitle.length < MIN_TITLE_CHARS || trimmedDesc.length < MIN_DESC_CHARS) {
      return;
    }

    const label = CATEGORY_LABELS[category];
    const categoryName = t(`category${category.charAt(0).toUpperCase() + category.slice(1)}`);

    const body = [
      `## ${t("descriptionHeading")}`,
      "",
      trimmedDesc,
      "",
      "---",
      `**${t("categoryLabel")}:** ${categoryName}`,
      `*${t("issueFooter")}*`,
    ].join("\n");

    const params = new URLSearchParams({
      title: trimmedTitle,
      body,
      labels: label,
    });

    window.open(`${GITHUB_NEW_ISSUE_URL}?${params}`, "_blank");
    onClose();
  };

  const canSubmit = title.trim().length >= MIN_TITLE_CHARS
    && description.trim().length >= MIN_DESC_CHARS;
  const charCount = description.length;
  const charWarning = charCount >= 4500;

  const footer = (
    <>
      <button className="feedback-btn feedback-btn-secondary" onClick={onClose}>
        {tCommon("cancel")}
      </button>
      <button
        className="feedback-btn feedback-btn-primary"
        onClick={handleSubmit}
        disabled={!canSubmit}
      >
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M9 19c-5 1.5-5-2.5-7-3m14 6v-3.87a3.37 3.37 0 0 0-.94-2.61c3.14-.35 6.44-1.54 6.44-7A5.44 5.44 0 0 0 20 4.77 5.07 5.07 0 0 0 19.91 1S18.73.65 16 2.48a13.38 13.38 0 0 0-7 0C6.27.65 5.09 1 5.09 1A5.07 5.07 0 0 0 5 4.77a5.44 5.44 0 0 0-1.5 3.78c0 5.42 3.3 6.61 6.44 7A3.37 3.37 0 0 0 9 18.13V22" />
        </svg>
        {t("submit")}
      </button>
    </>
  );

  return (
    <Modal open={open} onClose={onClose} title={t("title")} width={480} className="feedback-dialog" footer={footer}>
      <div className="feedback-content">
        <p className="feedback-intro">{t("intro")}</p>

        <div className="feedback-section">
          <div className="feedback-categories">
            {CATEGORIES.map((cat) => (
              <button
                key={cat}
                className={`feedback-category${category === cat ? " active" : ""}`}
                onClick={() => setCategory(cat)}
              >
                {t(`category${cat.charAt(0).toUpperCase() + cat.slice(1)}`)}
              </button>
            ))}
          </div>
        </div>

        <div className="feedback-section">
          <label className="feedback-field-label">
            {t("issueTitle")} <span className="feedback-required">*</span>
          </label>
          <input
            type="text"
            className="feedback-input"
            placeholder={t("issueTitlePlaceholder")}
            value={title}
            onChange={(e) => setTitle(e.target.value)}
          />
        </div>

        <div className="feedback-section">
          <label className="feedback-field-label">
            {t("issueDescription")} <span className="feedback-required">*</span>
          </label>
          <textarea
            className="feedback-textarea"
            placeholder={t("descriptionPlaceholder")}
            value={description}
            onChange={(e) => setDescription(e.target.value.slice(0, MAX_DESC_CHARS))}
            rows={6}
          />
          <div className={`feedback-char-count${charWarning ? " warning" : ""}`}>
            {charCount}/{MAX_DESC_CHARS}
          </div>
        </div>

        <div className="feedback-gh-note">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <circle cx="12" cy="12" r="10" />
            <line x1="12" y1="16" x2="12" y2="12" />
            <line x1="12" y1="8" x2="12.01" y2="8" />
          </svg>
          <span>{t("ghNote")}</span>
        </div>
      </div>
    </Modal>
  );
}
