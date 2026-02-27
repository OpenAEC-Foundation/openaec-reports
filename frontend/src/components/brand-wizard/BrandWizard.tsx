import { useEffect } from "react";
import { useBrandWizardStore } from "@/stores/brandWizardStore";
import { StepUpload } from "./StepUpload";
import { StepDiffReview } from "./StepDiffReview";
import { StepGenerate } from "./StepGenerate";

// ---------- Step indicator ----------

interface StepIndicatorProps {
  step: number;
  current: number;
  label: string;
}

function StepIndicator({ step, current, label }: StepIndicatorProps) {
  const isActive = step === current;
  const isCompleted = step < current;

  return (
    <div
      className={`flex items-center gap-2 ${
        isActive
          ? "text-blue-600"
          : isCompleted
            ? "text-green-600"
            : "text-gray-400"
      }`}
    >
      <div
        className={`flex h-8 w-8 items-center justify-center rounded-full text-sm font-medium ${
          isActive
            ? "bg-blue-100 text-blue-600 ring-2 ring-blue-600"
            : isCompleted
              ? "bg-green-100 text-green-600"
              : "bg-gray-100"
        }`}
      >
        {isCompleted ? (
          <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" strokeWidth={2.5} stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" d="M4.5 12.75l6 6 9-13.5" />
          </svg>
        ) : (
          step
        )}
      </div>
      <span className="text-sm font-medium">{label}</span>
    </div>
  );
}

// ---------- Main wizard ----------

export function BrandWizard() {
  const currentStep = useBrandWizardStore((s) => s.currentStep);
  const reset = useBrandWizardStore((s) => s.reset);

  // Reset wizard state when component unmounts
  useEffect(() => {
    return () => {
      // Don't reset on unmount — user might navigate back
    };
  }, []);

  return (
    <div className="flex h-full flex-col bg-gray-50">
      {/* Header with progress indicator */}
      <div className="flex items-center justify-between border-b border-gray-200 bg-white px-6 py-4">
        <div className="flex items-center gap-4">
          <StepIndicator step={1} current={currentStep} label="Upload" />
          <div className="h-px w-8 bg-gray-300" />
          <StepIndicator step={2} current={currentStep} label="Review" />
          <div className="h-px w-8 bg-gray-300" />
          <StepIndicator step={3} current={currentStep} label="Genereer" />
        </div>

        <button
          onClick={reset}
          className="rounded-md border border-gray-300 px-3 py-1.5 text-xs font-medium text-gray-500 transition-colors hover:bg-gray-50 hover:text-gray-700"
        >
          Reset wizard
        </button>
      </div>

      {/* Step content */}
      <div className="flex-1 overflow-auto p-6">
        {currentStep === 1 && <StepUpload />}
        {currentStep === 2 && <StepDiffReview />}
        {currentStep === 3 && <StepGenerate />}
      </div>
    </div>
  );
}
