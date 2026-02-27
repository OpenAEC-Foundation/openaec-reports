import type { DetectedField } from "@/api/brandApi";

interface FieldOverlayProps {
  fields: DetectedField[];
  imageUrl: string;
  pdfWidth: number;
  pdfHeight: number;
  activeFieldId: string | null;
  onFieldClick: (fieldId: string) => void;
  onFieldHover: (fieldId: string | null) => void;
}

export function FieldOverlay({
  fields,
  imageUrl,
  pdfWidth,
  pdfHeight,
  activeFieldId,
  onFieldClick,
  onFieldHover,
}: FieldOverlayProps) {
  return (
    <div className="relative inline-block">
      <img
        src={imageUrl}
        alt="PDF preview"
        className="w-full"
        draggable={false}
      />
      <svg
        className="absolute inset-0 h-full w-full"
        viewBox={`0 0 ${pdfWidth} ${pdfHeight}`}
        preserveAspectRatio="none"
      >
        {fields.map((field) => {
          const isActive = activeFieldId === field.id;
          return (
            <rect
              key={field.id}
              x={field.x_pt}
              y={field.y_pt}
              width={field.width_pt}
              height={field.height_pt}
              fill={isActive ? "rgba(239, 68, 68, 0.3)" : "rgba(239, 68, 68, 0.1)"}
              stroke={isActive ? "#ef4444" : "rgba(248, 113, 113, 0.6)"}
              strokeWidth={isActive ? 2 : 1}
              className="cursor-pointer transition-colors"
              onClick={() => onFieldClick(field.id)}
              onMouseEnter={() => onFieldHover(field.id)}
              onMouseLeave={() => onFieldHover(null)}
            >
              <title>{field.sample_text}</title>
            </rect>
          );
        })}
      </svg>
    </div>
  );
}
