interface BlockIconProps {
  type: string;
  className?: string;
}

export function BlockIcon({ type, className = 'h-4 w-4' }: BlockIconProps) {
  switch (type) {
    case 'paragraph':
      // Horizontal text lines
      return (
        <svg className={className} viewBox="0 0 16 16" fill="currentColor">
          <rect x="1" y="2" width="14" height="1.5" rx="0.5" />
          <rect x="1" y="6" width="14" height="1.5" rx="0.5" />
          <rect x="1" y="10" width="10" height="1.5" rx="0.5" />
        </svg>
      );
    case 'calculation':
      // fx symbol
      return (
        <svg className={className} viewBox="0 0 16 16" fill="currentColor">
          <path d="M2.5 2C2.5 1.45 2.95 1 3.5 1H6.5C7.05 1 7.5 1.45 7.5 2C7.5 2.55 7.05 3 6.5 3H5.5L4.5 8H6C6.55 8 7 8.45 7 9C7 9.55 6.55 10 6 10H4L3 15H3.5C3.5 15 2 15 2 15L3 10H1.5C0.95 10 0.5 9.55 0.5 9C0.5 8.45 0.95 8 1.5 8H3.5L4.5 3H3.5C2.95 3 2.5 2.55 2.5 2Z" />
          <path d="M9 5L11.5 8L9 11H11L12.5 9L14 11H16L13.5 8L16 5H14L12.5 7L11 5H9Z" />
        </svg>
      );
    case 'check':
      // Checkmark in square
      return (
        <svg className={className} viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5">
          <rect x="1.5" y="1.5" width="13" height="13" rx="2" />
          <path d="M4.5 8L7 10.5L11.5 5.5" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      );
    case 'table':
      // Grid/raster
      return (
        <svg className={className} viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.2">
          <rect x="1.5" y="1.5" width="13" height="13" rx="1.5" />
          <line x1="1.5" y1="5.5" x2="14.5" y2="5.5" />
          <line x1="1.5" y1="10" x2="14.5" y2="10" />
          <line x1="6" y1="1.5" x2="6" y2="14.5" />
          <line x1="10.5" y1="1.5" x2="10.5" y2="14.5" />
        </svg>
      );
    case 'image':
      // Landscape with sun
      return (
        <svg className={className} viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.2">
          <rect x="1.5" y="2.5" width="13" height="11" rx="1.5" />
          <circle cx="5" cy="6" r="1.5" fill="currentColor" stroke="none" />
          <path d="M1.5 11L5 8L8 11L11 7.5L14.5 11" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      );
    case 'map':
      // Pin/marker
      return (
        <svg className={className} viewBox="0 0 16 16" fill="currentColor">
          <path d="M8 1C5.24 1 3 3.24 3 6C3 9.75 8 15 8 15C8 15 13 9.75 13 6C13 3.24 10.76 1 8 1ZM8 7.75C7.03 7.75 6.25 6.97 6.25 6C6.25 5.03 7.03 4.25 8 4.25C8.97 4.25 9.75 5.03 9.75 6C9.75 6.97 8.97 7.75 8 7.75Z" />
        </svg>
      );
    case 'spacer':
      // Vertical arrows apart
      return (
        <svg className={className} viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5">
          <path d="M8 1.5V6M8 1.5L5.5 4M8 1.5L10.5 4" strokeLinecap="round" strokeLinejoin="round" />
          <path d="M8 14.5V10M8 14.5L5.5 12M8 14.5L10.5 12" strokeLinecap="round" strokeLinejoin="round" />
          <line x1="3" y1="8" x2="13" y2="8" strokeLinecap="round" strokeDasharray="2 2" />
        </svg>
      );
    case 'page_break':
      // Horizontal dashed line with arrow down
      return (
        <svg className={className} viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5">
          <line x1="1" y1="7" x2="5" y2="7" strokeLinecap="round" />
          <line x1="11" y1="7" x2="15" y2="7" strokeLinecap="round" />
          <path d="M8 4V12M8 12L5.5 9.5M8 12L10.5 9.5" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      );
    case 'bullet_list':
      // Bullet list with dots
      return (
        <svg className={className} viewBox="0 0 16 16" fill="currentColor">
          <circle cx="3" cy="4" r="1.5" />
          <rect x="6" y="3" width="9" height="2" rx="0.5" />
          <circle cx="3" cy="8" r="1.5" />
          <rect x="6" y="7" width="9" height="2" rx="0.5" />
          <circle cx="3" cy="12" r="1.5" />
          <rect x="6" y="11" width="9" height="2" rx="0.5" />
        </svg>
      );
    case 'heading_2':
      // H2 text
      return (
        <svg className={className} viewBox="0 0 16 16" fill="currentColor">
          <text x="1" y="13" fontSize="12" fontWeight="bold" fontFamily="sans-serif">H2</text>
        </svg>
      );
    case 'raw_flowable':
      // Code brackets
      return (
        <svg className={className} viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5">
          <path d="M5 3L1.5 8L5 13" strokeLinecap="round" strokeLinejoin="round" />
          <path d="M11 3L14.5 8L11 13" strokeLinecap="round" strokeLinejoin="round" />
          <line x1="9.5" y1="2" x2="6.5" y2="14" strokeLinecap="round" />
        </svg>
      );
    default:
      return (
        <svg className={className} viewBox="0 0 16 16" fill="currentColor">
          <circle cx="8" cy="8" r="3" />
        </svg>
      );
  }
}
