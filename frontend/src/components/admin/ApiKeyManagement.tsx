import { useEffect, useState } from "react";
import { useAdminStore } from "@/stores/adminStore";
import type { CreateApiKeyPayload } from "@/services/api";

export function ApiKeyManagement() {
  const apiKeys = useAdminStore((s) => s.apiKeys);
  const apiKeysLoading = useAdminStore((s) => s.apiKeysLoading);
  const users = useAdminStore((s) => s.users);
  const loadApiKeys = useAdminStore((s) => s.loadApiKeys);
  const createApiKey = useAdminStore((s) => s.createApiKey);
  const revokeApiKey = useAdminStore((s) => s.revokeApiKey);
  const deleteApiKey = useAdminStore((s) => s.deleteApiKey);

  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState<CreateApiKeyPayload>({
    name: "",
    user_id: "",
  });
  const [plaintextKey, setPlaintextKey] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);
  const [confirmRevoke, setConfirmRevoke] = useState<string | null>(null);
  const [confirmDelete, setConfirmDelete] = useState<string | null>(null);

  useEffect(() => {
    loadApiKeys();
  }, [loadApiKeys]);

  function getUserName(userId: string): string {
    const user = users.find((u) => u.id === userId);
    return user?.username ?? userId.slice(0, 8) + "...";
  }

  async function handleCreate() {
    if (!form.name || !form.user_id) return;
    const plaintext = await createApiKey(form);
    if (plaintext) {
      setPlaintextKey(plaintext);
      setShowForm(false);
      setForm({ name: "", user_id: "" });
    }
  }

  async function handleRevoke(keyId: string) {
    const ok = await revokeApiKey(keyId);
    if (ok) setConfirmRevoke(null);
  }

  async function handleDelete(keyId: string) {
    const ok = await deleteApiKey(keyId);
    if (ok) setConfirmDelete(null);
  }

  async function handleCopy() {
    if (!plaintextKey) return;
    await navigator.clipboard.writeText(plaintextKey);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  if (apiKeysLoading) {
    return <LoadingSpinner label="API keys laden..." />;
  }

  return (
    <div>
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold text-gray-800">
          API Keys ({apiKeys.length})
        </h2>
        <button
          onClick={() => {
            setShowForm(!showForm);
            setPlaintextKey(null);
          }}
          className="rounded-md bg-purple-600 px-4 py-2 text-sm font-medium text-white hover:bg-purple-700 transition-colors"
        >
          {showForm ? "Annuleren" : "Nieuwe API key"}
        </button>
      </div>

      {/* Plaintext key banner — eenmalig zichtbaar na aanmaken */}
      {plaintextKey && (
        <div className="mb-4 rounded-lg border border-green-200 bg-green-50 p-4">
          <p className="text-sm font-semibold text-green-800 mb-2">
            API key aangemaakt — kopieer deze nu! Deze wordt niet meer getoond.
          </p>
          <div className="flex items-center gap-2">
            <code className="flex-1 rounded bg-white px-3 py-2 text-sm font-mono border border-green-200 select-all break-all">
              {plaintextKey}
            </code>
            <button
              onClick={handleCopy}
              className="rounded-md bg-green-600 px-3 py-2 text-sm font-medium text-white hover:bg-green-700 transition-colors whitespace-nowrap"
            >
              {copied ? "Gekopieerd!" : "Kopieer"}
            </button>
          </div>
          <button
            onClick={() => setPlaintextKey(null)}
            className="mt-2 text-xs text-green-600 hover:text-green-800"
          >
            Sluiten
          </button>
        </div>
      )}

      {/* Create form */}
      {showForm && (
        <div className="mb-6 rounded-lg border border-gray-200 bg-gray-50 p-4">
          <h3 className="text-sm font-semibold text-gray-700 mb-3">
            Nieuwe API key
          </h3>
          <div className="grid grid-cols-2 gap-3">
            <Input
              label="Naam *"
              value={form.name}
              onChange={(v) => setForm({ ...form, name: v })}
              placeholder="bijv. pyRevit productie"
            />
            <Select
              label="Gebruiker *"
              value={form.user_id}
              options={[
                { value: "", label: "(selecteer)" },
                ...users.map((u) => ({
                  value: u.id,
                  label: u.username,
                })),
              ]}
              onChange={(v) => setForm({ ...form, user_id: v })}
            />
          </div>
          <div className="mt-4 flex justify-end">
            <button
              onClick={handleCreate}
              disabled={!form.name || !form.user_id}
              className="rounded-md bg-purple-600 px-4 py-2 text-sm font-medium text-white hover:bg-purple-700 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
            >
              Aanmaken
            </button>
          </div>
        </div>
      )}

      {/* API keys table */}
      {apiKeys.length === 0 ? (
        <div className="text-center py-12 text-sm text-gray-500">
          Nog geen API keys aangemaakt.
        </div>
      ) : (
        <div className="overflow-hidden rounded-lg border border-gray-200">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <Th>Naam</Th>
                <Th>Gebruiker</Th>
                <Th>Prefix</Th>
                <Th>Aangemaakt</Th>
                <Th>Status</Th>
                <Th>Acties</Th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200 bg-white">
              {apiKeys.map((key) => (
                <tr
                  key={key.id}
                  className={!key.is_active ? "bg-gray-50 opacity-60" : ""}
                >
                  <Td className="font-medium">{key.name}</Td>
                  <Td>{getUserName(key.user_id)}</Td>
                  <Td>
                    <code className="text-xs bg-gray-100 px-1.5 py-0.5 rounded">
                      {key.key_prefix}...
                    </code>
                  </Td>
                  <Td>{formatDate(key.created_at)}</Td>
                  <Td>
                    <span
                      className={`rounded-full px-2 py-0.5 text-xs font-medium ${
                        key.is_active
                          ? "bg-green-100 text-green-700"
                          : "bg-red-100 text-red-700"
                      }`}
                    >
                      {key.is_active ? "Actief" : "Ingetrokken"}
                    </span>
                  </Td>
                  <Td>
                    <div className="flex items-center gap-1">
                      {key.is_active && (
                        <button
                          onClick={() => setConfirmRevoke(key.id)}
                          className="rounded px-2 py-1 text-xs text-orange-600 hover:bg-orange-50"
                          title="Intrekken (deactiveren)"
                        >
                          Intrekken
                        </button>
                      )}
                      <button
                        onClick={() => setConfirmDelete(key.id)}
                        className="rounded px-2 py-1 text-xs text-red-600 hover:bg-red-50"
                        title="Permanent verwijderen"
                      >
                        Verwijder
                      </button>
                    </div>
                  </Td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Confirm revoke dialog */}
      {confirmRevoke && (
        <Dialog
          title="API key intrekken"
          onClose={() => setConfirmRevoke(null)}
        >
          <p className="text-sm text-gray-600">
            Weet je zeker dat je deze API key wilt intrekken? De key wordt
            gedeactiveerd en kan niet meer gebruikt worden voor authenticatie.
          </p>
          <div className="mt-4 flex justify-end gap-2">
            <button
              onClick={() => setConfirmRevoke(null)}
              className="rounded-md border border-gray-300 px-4 py-2 text-sm text-gray-700 hover:bg-gray-50"
            >
              Annuleren
            </button>
            <button
              onClick={() => handleRevoke(confirmRevoke)}
              className="rounded-md bg-orange-600 px-4 py-2 text-sm font-medium text-white hover:bg-orange-700"
            >
              Intrekken
            </button>
          </div>
        </Dialog>
      )}

      {/* Confirm delete dialog */}
      {confirmDelete && (
        <Dialog
          title="API key verwijderen"
          onClose={() => setConfirmDelete(null)}
        >
          <p className="text-sm text-gray-600">
            Weet je zeker dat je deze API key permanent wilt verwijderen? Dit kan
            niet ongedaan worden.
          </p>
          <div className="mt-4 flex justify-end gap-2">
            <button
              onClick={() => setConfirmDelete(null)}
              className="rounded-md border border-gray-300 px-4 py-2 text-sm text-gray-700 hover:bg-gray-50"
            >
              Annuleren
            </button>
            <button
              onClick={() => handleDelete(confirmDelete)}
              className="rounded-md bg-red-600 px-4 py-2 text-sm font-medium text-white hover:bg-red-700"
            >
              Verwijderen
            </button>
          </div>
        </Dialog>
      )}
    </div>
  );
}

// ---------- Helpers ----------

function formatDate(iso: string): string {
  try {
    const d = new Date(iso);
    return d.toLocaleDateString("nl-NL", {
      day: "2-digit",
      month: "2-digit",
      year: "numeric",
    });
  } catch {
    return iso;
  }
}

// ---------- Shared sub-components ----------

function Th({ children }: { children: React.ReactNode }) {
  return (
    <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
      {children}
    </th>
  );
}

function Td({
  children,
  className = "",
}: {
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <td className={`px-4 py-3 text-sm text-gray-700 ${className}`}>
      {children}
    </td>
  );
}

function Input({
  label,
  value,
  onChange,
  placeholder,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  placeholder?: string;
}) {
  return (
    <label className="block">
      <span className="text-xs font-medium text-gray-600">{label}</span>
      <input
        type="text"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-1.5 text-sm shadow-sm focus:border-purple-500 focus:ring-1 focus:ring-purple-500"
      />
    </label>
  );
}

function Select({
  label,
  value,
  options,
  onChange,
}: {
  label: string;
  value: string;
  options: { value: string; label: string }[];
  onChange: (v: string) => void;
}) {
  return (
    <label className="block">
      <span className="text-xs font-medium text-gray-600">{label}</span>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-1.5 text-sm shadow-sm focus:border-purple-500 focus:ring-1 focus:ring-purple-500"
      >
        {options.map((o) => (
          <option key={o.value} value={o.value}>
            {o.label}
          </option>
        ))}
      </select>
    </label>
  );
}

function Dialog({
  title,
  children,
  onClose,
}: {
  title: string;
  children: React.ReactNode;
  onClose: () => void;
}) {
  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/30"
      onClick={onClose}
    >
      <div
        className="w-full max-w-md rounded-xl bg-white p-6 shadow-xl"
        onClick={(e) => e.stopPropagation()}
      >
        <h3 className="text-lg font-semibold text-gray-900 mb-4">{title}</h3>
        {children}
      </div>
    </div>
  );
}

function LoadingSpinner({ label }: { label: string }) {
  return (
    <div className="flex items-center gap-2 text-sm text-gray-500 py-8">
      <svg className="h-4 w-4 animate-spin" fill="none" viewBox="0 0 24 24">
        <circle
          className="opacity-25"
          cx="12"
          cy="12"
          r="10"
          stroke="currentColor"
          strokeWidth="4"
        />
        <path
          className="opacity-75"
          fill="currentColor"
          d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
        />
      </svg>
      {label}
    </div>
  );
}
