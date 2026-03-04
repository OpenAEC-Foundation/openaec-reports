import { useState, useEffect } from 'react';
import { useReportStore } from '@/stores/reportStore';
import { useAuthStore } from '@/stores/authStore';
import { ToggleSwitch } from './ToggleSwitch';
import brand from '@/config/brand';
import type { Colofon, RevisionEntry } from '@/types/report';

const inputClass =
  'w-full rounded border border-gray-200 px-2 py-1.5 text-sm focus:border-blue-300 focus:ring-2 focus:ring-blue-100 outline-none';

const labelClass = 'block text-xs font-medium text-gray-500 mb-1';

const FASE_OPTIONS = [
  'Haalbaarheid',
  'Voorlopig Ontwerp',
  'Definitief Ontwerp',
  'Uitvoering',
];

const STATUS_OPTIONS = ['Concept', 'Definitief', 'Revisie'];

function today(): string {
  return new Date().toISOString().slice(0, 10);
}

export function ColofonForm() {
  const colofon = useReportStore((s) => s.report.colofon);
  const setColofon = useReportStore((s) => s.setColofon);
  const user = useAuthStore((s) => s.user);

  // Local state for text inputs (commit on blur)
  const [local, setLocal] = useState({
    opdrachtgever_contact: colofon.opdrachtgever_contact ?? '',
    opdrachtgever_naam: colofon.opdrachtgever_naam ?? '',
    opdrachtgever_adres: colofon.opdrachtgever_adres ?? '',
    adviseur_bedrijf: colofon.adviseur_bedrijf ?? brand.fullName,
    adviseur_naam: colofon.adviseur_naam ?? '',
    adviseur_email: colofon.adviseur_email ?? '',
    adviseur_telefoon: colofon.adviseur_telefoon ?? '',
    adviseur_functie: colofon.adviseur_functie ?? '',
    adviseur_registratie: colofon.adviseur_registratie ?? '',
    normen: colofon.normen ?? '',
    documentgegevens: colofon.documentgegevens ?? '',
    datum: colofon.datum ?? today(),
    fase: colofon.fase ?? '',
    status_colofon: colofon.status_colofon ?? '',
    kenmerk: colofon.kenmerk ?? '',
    disclaimer: colofon.disclaimer ?? '',
  });

  // Auto-fill adviseur velden vanuit user profiel (alleen lege velden)
  useEffect(() => {
    if (!user) return;
    const updates: Partial<Colofon> = {};
    if (!colofon.adviseur_naam && user.display_name) {
      updates.adviseur_naam = user.display_name;
    }
    if (!colofon.adviseur_email && user.email) {
      updates.adviseur_email = user.email;
    }
    if (!colofon.adviseur_telefoon && user.phone) {
      updates.adviseur_telefoon = user.phone;
    }
    if (!colofon.adviseur_functie && user.job_title) {
      updates.adviseur_functie = user.job_title;
    }
    if (!colofon.adviseur_registratie && user.registration_number) {
      updates.adviseur_registratie = user.registration_number;
    }
    if (!colofon.adviseur_bedrijf && user.company) {
      updates.adviseur_bedrijf = user.company;
    }
    if (Object.keys(updates).length > 0) {
      setColofon({ ...colofon, ...updates });
    }
    // Alleen bij eerste mount of user wijziging
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user]);

  // Sync local state when store changes externally
  useEffect(() => {
    setLocal({
      opdrachtgever_contact: colofon.opdrachtgever_contact ?? '',
      opdrachtgever_naam: colofon.opdrachtgever_naam ?? '',
      opdrachtgever_adres: colofon.opdrachtgever_adres ?? '',
      adviseur_bedrijf: colofon.adviseur_bedrijf ?? brand.fullName,
      adviseur_naam: colofon.adviseur_naam ?? '',
      adviseur_email: colofon.adviseur_email ?? '',
      adviseur_telefoon: colofon.adviseur_telefoon ?? '',
      adviseur_functie: colofon.adviseur_functie ?? '',
      adviseur_registratie: colofon.adviseur_registratie ?? '',
      normen: colofon.normen ?? '',
      documentgegevens: colofon.documentgegevens ?? '',
      datum: colofon.datum ?? today(),
      fase: colofon.fase ?? '',
      status_colofon: colofon.status_colofon ?? '',
      kenmerk: colofon.kenmerk ?? '',
      disclaimer: colofon.disclaimer ?? '',
    });
  }, [colofon]);

  function updateColofon(updates: Partial<Colofon>) {
    setColofon({ ...colofon, ...updates });
  }

  function handleToggle() {
    updateColofon({ enabled: !colofon.enabled });
  }

  function handleLocalChange(field: keyof typeof local, value: string) {
    setLocal((prev) => ({ ...prev, [field]: value }));
  }

  function handleBlur(field: keyof typeof local) {
    const value = local[field];
    const current = colofon[field as keyof Colofon];
    if (value !== (current ?? '')) {
      updateColofon({ [field]: value || undefined });
    }
  }

  // --- Revision history ---

  const revisions = colofon.revision_history ?? [];

  const sortedRevisions = [...revisions].sort((a, b) => {
    const numA = parseFloat(a.version) || 0;
    const numB = parseFloat(b.version) || 0;
    return numB - numA;
  });

  function updateRevisions(newRevisions: RevisionEntry[]) {
    updateColofon({ revision_history: newRevisions.length > 0 ? newRevisions : undefined });
  }

  function addRevision() {
    const maxVersion = revisions.reduce((max, r) => {
      const num = parseFloat(r.version);
      return isNaN(num) ? max : Math.max(max, num);
    }, 0);
    const nextVersion = (maxVersion + 1).toFixed(1);

    const newEntry: RevisionEntry = {
      version: nextVersion,
      date: today(),
      author: '',
      description: '',
    };
    updateRevisions([...revisions, newEntry]);
  }

  function updateRevision(index: number, updates: Partial<RevisionEntry>) {
    const newRevisions = revisions.map((r, i) => (i === index ? { ...r, ...updates } : r));
    updateRevisions(newRevisions);
  }

  function removeRevision(index: number) {
    updateRevisions(revisions.filter((_, i) => i !== index));
  }

  function getOriginalIndex(sortedIdx: number): number {
    const sortedEntry = sortedRevisions[sortedIdx];
    if (!sortedEntry) return -1;
    return revisions.indexOf(sortedEntry);
  }

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      {/* Header + Toggle */}
      <div className="flex items-center justify-between border-b border-gray-100 pb-2">
        <h3 className="text-sm font-semibold text-gray-700">Colofon</h3>
        <ToggleSwitch checked={colofon.enabled !== false} onChange={handleToggle} label="Tonen" />
      </div>

      {colofon.enabled !== false && (
        <>
          {/* Sectie: Opdrachtgever */}
          <fieldset className="space-y-3">
            <legend className="text-xs font-semibold text-gray-400 uppercase tracking-wider">Opdrachtgever</legend>
            <div>
              <label className={labelClass}>Contactpersoon</label>
              <input
                type="text"
                className={inputClass}
                value={local.opdrachtgever_contact}
                onChange={(e) => handleLocalChange('opdrachtgever_contact', e.target.value)}
                onBlur={() => handleBlur('opdrachtgever_contact')}
                placeholder="Dhr. P. van der Berg"
              />
            </div>
            <div>
              <label className={labelClass}>Bedrijfsnaam</label>
              <input
                type="text"
                className={inputClass}
                value={local.opdrachtgever_naam}
                onChange={(e) => handleLocalChange('opdrachtgever_naam', e.target.value)}
                onBlur={() => handleBlur('opdrachtgever_naam')}
                placeholder="Bedrijfsnaam B.V."
              />
            </div>
            <div>
              <label className={labelClass}>Adres</label>
              <textarea
                className={`${inputClass} min-h-[60px] resize-y`}
                value={local.opdrachtgever_adres}
                onChange={(e) => handleLocalChange('opdrachtgever_adres', e.target.value)}
                onBlur={() => handleBlur('opdrachtgever_adres')}
                placeholder={"Straat 12,\n1234 AB Stad"}
                rows={2}
              />
            </div>
          </fieldset>

          {/* Sectie: Adviseur */}
          <fieldset className="space-y-3">
            <legend className="text-xs font-semibold text-gray-400 uppercase tracking-wider">Adviseur</legend>
            <div>
              <label className={labelClass}>Bedrijf</label>
              <input
                type="text"
                className={inputClass}
                value={local.adviseur_bedrijf}
                onChange={(e) => handleLocalChange('adviseur_bedrijf', e.target.value)}
                onBlur={() => handleBlur('adviseur_bedrijf')}
                placeholder={brand.fullName}
              />
            </div>
            <div>
              <label className={labelClass}>Uitvoerend adviseur</label>
              <input
                type="text"
                className={inputClass}
                value={local.adviseur_naam}
                onChange={(e) => handleLocalChange('adviseur_naam', e.target.value)}
                onBlur={() => handleBlur('adviseur_naam')}
                placeholder="Ir. S. de Vries"
              />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className={labelClass}>E-mail</label>
                <input
                  type="email"
                  className={inputClass}
                  value={local.adviseur_email}
                  onChange={(e) => handleLocalChange('adviseur_email', e.target.value)}
                  onBlur={() => handleBlur('adviseur_email')}
                  placeholder="adviseur@bedrijf.nl"
                />
              </div>
              <div>
                <label className={labelClass}>Telefoon</label>
                <input
                  type="tel"
                  className={inputClass}
                  value={local.adviseur_telefoon}
                  onChange={(e) => handleLocalChange('adviseur_telefoon', e.target.value)}
                  onBlur={() => handleBlur('adviseur_telefoon')}
                  placeholder="+31 6 12345678"
                />
              </div>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className={labelClass}>Functie</label>
                <input
                  type="text"
                  className={inputClass}
                  value={local.adviseur_functie}
                  onChange={(e) => handleLocalChange('adviseur_functie', e.target.value)}
                  onBlur={() => handleBlur('adviseur_functie')}
                  placeholder="Constructeur"
                />
              </div>
              <div>
                <label className={labelClass}>Registratienummer</label>
                <input
                  type="text"
                  className={inputClass}
                  value={local.adviseur_registratie}
                  onChange={(e) => handleLocalChange('adviseur_registratie', e.target.value)}
                  onBlur={() => handleBlur('adviseur_registratie')}
                  placeholder="IBS-12345"
                />
              </div>
            </div>
          </fieldset>

          {/* Sectie: Document */}
          <fieldset className="space-y-3">
            <legend className="text-xs font-semibold text-gray-400 uppercase tracking-wider">Document</legend>
            <div>
              <label className={labelClass}>Toegepaste normen</label>
              <textarea
                className={`${inputClass} min-h-[60px] resize-y`}
                value={local.normen}
                onChange={(e) => handleLocalChange('normen', e.target.value)}
                onBlur={() => handleBlur('normen')}
                placeholder="Eurocode, NEN-EN 1990"
                rows={2}
              />
            </div>
            <div>
              <label className={labelClass}>Documentgegevens</label>
              <input
                type="text"
                className={inputClass}
                value={local.documentgegevens}
                onChange={(e) => handleLocalChange('documentgegevens', e.target.value)}
                onBlur={() => handleBlur('documentgegevens')}
                placeholder="Constructief advies, pg 1-14"
              />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className={labelClass}>Datum</label>
                <input
                  type="date"
                  className={inputClass}
                  value={local.datum}
                  onChange={(e) => {
                    handleLocalChange('datum', e.target.value);
                    updateColofon({ datum: e.target.value || undefined });
                  }}
                />
              </div>
              <div>
                <label className={labelClass}>Kenmerk</label>
                <input
                  type="text"
                  className={inputClass}
                  value={local.kenmerk}
                  onChange={(e) => handleLocalChange('kenmerk', e.target.value)}
                  onBlur={() => handleBlur('kenmerk')}
                  placeholder="2801-CA-01"
                />
              </div>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className={labelClass}>Fase in bouwproces</label>
                <select
                  className={inputClass}
                  value={local.fase}
                  onChange={(e) => {
                    handleLocalChange('fase', e.target.value);
                    updateColofon({ fase: e.target.value || undefined });
                  }}
                >
                  <option value="">— Selecteer fase —</option>
                  {FASE_OPTIONS.map((f) => (
                    <option key={f} value={f}>{f}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className={labelClass}>Status</label>
                <select
                  className={inputClass}
                  value={local.status_colofon}
                  onChange={(e) => {
                    handleLocalChange('status_colofon', e.target.value);
                    updateColofon({ status_colofon: e.target.value || undefined });
                  }}
                >
                  <option value="">— Selecteer status —</option>
                  {STATUS_OPTIONS.map((s) => (
                    <option key={s} value={s}>{s}</option>
                  ))}
                </select>
              </div>
            </div>
          </fieldset>

          {/* Revisiegeschiedenis */}
          <div>
            <label className={labelClass}>Revisiegeschiedenis</label>
            <div className="rounded-lg border border-gray-200 overflow-hidden">
              <div className="grid grid-cols-[60px_100px_1fr_1fr_32px] gap-px bg-gray-100 text-xs font-medium text-gray-500">
                <div className="bg-gray-50 px-2 py-1.5">Versie</div>
                <div className="bg-gray-50 px-2 py-1.5">Datum</div>
                <div className="bg-gray-50 px-2 py-1.5">Auteur</div>
                <div className="bg-gray-50 px-2 py-1.5">Omschrijving</div>
                <div className="bg-gray-50" />
              </div>

              {sortedRevisions.length === 0 && (
                <div className="px-3 py-4 text-center text-sm text-gray-400 italic">
                  Geen revisies
                </div>
              )}

              {sortedRevisions.map((rev, sortedIdx) => {
                const origIdx = getOriginalIndex(sortedIdx);
                return (
                  <RevisionRow
                    key={`${origIdx}-${rev.version}`}
                    revision={rev}
                    onUpdate={(updates) => updateRevision(origIdx, updates)}
                    onRemove={() => removeRevision(origIdx)}
                  />
                );
              })}
            </div>

            <button
              onClick={addRevision}
              className="mt-2 flex items-center gap-1 rounded px-2 py-1 text-xs text-gray-400 hover:bg-blue-50 hover:text-blue-600 transition-colors"
            >
              <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
              </svg>
              Revisie toevoegen
            </button>
          </div>

          {/* Disclaimer */}
          <div>
            <label className={labelClass}>Disclaimer</label>
            <textarea
              className={`${inputClass} min-h-[80px] resize-y`}
              value={local.disclaimer}
              onChange={(e) => handleLocalChange('disclaimer', e.target.value)}
              onBlur={() => handleBlur('disclaimer')}
              placeholder="Disclaimer tekst voor het colofon"
              rows={3}
            />
          </div>
        </>
      )}
    </div>
  );
}

// ---------- Revision row ----------

function RevisionRow({
  revision,
  onUpdate,
  onRemove,
}: {
  revision: RevisionEntry;
  onUpdate: (updates: Partial<RevisionEntry>) => void;
  onRemove: () => void;
}) {
  const [local, setLocal] = useState(revision);

  const cellClass = 'bg-white px-2 py-1';
  const cellInputClass =
    'w-full border-0 bg-transparent px-0 py-0 text-sm focus:ring-0 outline-none';

  function handleBlur(field: keyof RevisionEntry) {
    if (local[field] !== revision[field]) {
      onUpdate({ [field]: local[field] });
    }
  }

  return (
    <div className="group grid grid-cols-[60px_100px_1fr_1fr_32px] gap-px bg-gray-100">
      <div className={cellClass}>
        <input
          type="text"
          className={cellInputClass}
          value={local.version}
          onChange={(e) => setLocal((p) => ({ ...p, version: e.target.value }))}
          onBlur={() => handleBlur('version')}
          placeholder="1.0"
        />
      </div>
      <div className={cellClass}>
        <input
          type="date"
          className={`${cellInputClass} text-xs`}
          value={local.date}
          onChange={(e) => {
            setLocal((p) => ({ ...p, date: e.target.value }));
            onUpdate({ date: e.target.value });
          }}
        />
      </div>
      <div className={cellClass}>
        <input
          type="text"
          className={cellInputClass}
          value={local.author ?? ''}
          onChange={(e) => setLocal((p) => ({ ...p, author: e.target.value }))}
          onBlur={() => handleBlur('author')}
          placeholder="Auteur"
        />
      </div>
      <div className={cellClass}>
        <input
          type="text"
          className={cellInputClass}
          value={local.description}
          onChange={(e) => setLocal((p) => ({ ...p, description: e.target.value }))}
          onBlur={() => handleBlur('description')}
          placeholder="Omschrijving"
        />
      </div>
      <div className={`${cellClass} flex items-center justify-center`}>
        <button
          onClick={onRemove}
          className="flex h-5 w-5 items-center justify-center rounded text-gray-300 opacity-0 group-hover:opacity-100 hover:bg-red-50 hover:text-red-500 transition-opacity"
          title="Verwijder revisie"
        >
          <svg className="h-3 w-3" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>
    </div>
  );
}
