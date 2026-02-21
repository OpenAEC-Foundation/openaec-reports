import { useState } from 'react';
import { MetadataForm } from './MetadataForm';
import { CoverForm } from './CoverForm';
import { ColofonForm } from './ColofonForm';
import { OptionsPanel } from './OptionsPanel';

type TabId = 'rapport' | 'voorblad' | 'colofon' | 'opties';

const TABS: { id: TabId; label: string }[] = [
  { id: 'rapport', label: 'Rapport' },
  { id: 'voorblad', label: 'Voorblad' },
  { id: 'colofon', label: 'Colofon' },
  { id: 'opties', label: 'Opties' },
];

export function MetadataTabs() {
  const [activeTab, setActiveTab] = useState<TabId>('rapport');

  return (
    <div className="flex-1 overflow-y-auto">
      {/* Tab bar */}
      <div className="sticky top-0 z-10 border-b border-gray-200 bg-white/95 backdrop-blur px-6 py-3">
        <div className="inline-flex rounded-lg bg-gray-100 p-0.5">
          {TABS.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`rounded-md px-3 py-1.5 text-xs font-medium transition-colors ${
                activeTab === tab.id
                  ? 'bg-white text-gray-900 shadow-sm'
                  : 'text-gray-500 hover:text-gray-700'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      {/* Tab content */}
      <div className="px-6 py-6">
        {activeTab === 'rapport' && <MetadataForm />}
        {activeTab === 'voorblad' && <CoverForm />}
        {activeTab === 'colofon' && <ColofonForm />}
        {activeTab === 'opties' && <OptionsPanel />}
      </div>
    </div>
  );
}
