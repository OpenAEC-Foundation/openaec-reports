import { useState } from "react";
import { useAdminStore } from "@/stores/adminStore";
import { useAuthStore } from "@/stores/authStore";
import type { AdminUser, CreateUserPayload } from "@/services/api";

const EMPTY_FORM: CreateUserPayload = {
  username: "",
  email: "",
  display_name: "",
  password: "",
  role: "user",
  tenant: "",
};

export function UserManagement() {
  const users = useAdminStore((s) => s.users);
  const usersLoading = useAdminStore((s) => s.usersLoading);
  const tenants = useAdminStore((s) => s.tenants);
  const createUser = useAdminStore((s) => s.createUser);
  const updateUser = useAdminStore((s) => s.updateUser);
  const deleteUser = useAdminStore((s) => s.deleteUser);
  const resetPassword = useAdminStore((s) => s.resetPassword);
  const currentUser = useAuthStore((s) => s.user);

  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState<CreateUserPayload>({ ...EMPTY_FORM });
  const [editingId, setEditingId] = useState<string | null>(null);
  const [resetId, setResetId] = useState<string | null>(null);
  const [newPassword, setNewPassword] = useState("");
  const [confirmDelete, setConfirmDelete] = useState<string | null>(null);

  async function handleCreate() {
    if (!form.username || !form.password) return;
    const user = await createUser(form);
    if (user) {
      setShowForm(false);
      setForm({ ...EMPTY_FORM });
    }
  }

  async function handleToggleActive(user: AdminUser) {
    await updateUser(user.id, { is_active: !user.is_active });
  }

  async function handleRoleChange(user: AdminUser, role: string) {
    await updateUser(user.id, { role });
  }

  async function handleResetPassword() {
    if (!resetId || !newPassword) return;
    const ok = await resetPassword(resetId, newPassword);
    if (ok) {
      setResetId(null);
      setNewPassword("");
    }
  }

  async function handleDelete(id: string) {
    const ok = await deleteUser(id);
    if (ok) setConfirmDelete(null);
  }

  if (usersLoading) {
    return <LoadingSpinner label="Gebruikers laden..." />;
  }

  return (
    <div>
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold text-gray-800">
          Gebruikers ({users.length})
        </h2>
        <button
          onClick={() => setShowForm(!showForm)}
          className="rounded-md bg-purple-600 px-4 py-2 text-sm font-medium text-white hover:bg-purple-700 transition-colors"
        >
          {showForm ? "Annuleren" : "Nieuwe gebruiker"}
        </button>
      </div>

      {/* Create form */}
      {showForm && (
        <div className="mb-6 rounded-lg border border-gray-200 bg-gray-50 p-4">
          <h3 className="text-sm font-semibold text-gray-700 mb-3">Nieuwe gebruiker</h3>
          <div className="grid grid-cols-2 gap-3">
            <Input
              label="Gebruikersnaam *"
              value={form.username}
              onChange={(v) => setForm({ ...form, username: v })}
            />
            <Input
              label="Wachtwoord *"
              type="password"
              value={form.password}
              onChange={(v) => setForm({ ...form, password: v })}
            />
            <Input
              label="E-mail"
              value={form.email ?? ""}
              onChange={(v) => setForm({ ...form, email: v })}
            />
            <Input
              label="Weergavenaam"
              value={form.display_name ?? ""}
              onChange={(v) => setForm({ ...form, display_name: v })}
            />
            <Select
              label="Rol"
              value={form.role ?? "user"}
              options={[
                { value: "user", label: "Gebruiker" },
                { value: "admin", label: "Admin" },
              ]}
              onChange={(v) => setForm({ ...form, role: v })}
            />
            <Select
              label="Tenant"
              value={form.tenant ?? ""}
              options={[
                { value: "", label: "(geen)" },
                ...tenants.map((t) => ({ value: t.name, label: t.name })),
              ]}
              onChange={(v) => setForm({ ...form, tenant: v })}
            />
          </div>
          <div className="mt-4 flex justify-end">
            <button
              onClick={handleCreate}
              disabled={!form.username || !form.password}
              className="rounded-md bg-purple-600 px-4 py-2 text-sm font-medium text-white hover:bg-purple-700 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
            >
              Aanmaken
            </button>
          </div>
        </div>
      )}

      {/* Users table */}
      <div className="overflow-hidden rounded-lg border border-gray-200">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <Th>Gebruikersnaam</Th>
              <Th>Weergavenaam</Th>
              <Th>E-mail</Th>
              <Th>Rol</Th>
              <Th>Tenant</Th>
              <Th>Status</Th>
              <Th>Acties</Th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200 bg-white">
            {users.map((user) => (
              <tr key={user.id} className={!user.is_active ? "bg-gray-50 opacity-60" : ""}>
                <Td className="font-medium">{user.username}</Td>
                <Td>
                  {editingId === user.id ? (
                    <InlineEdit
                      value={user.display_name}
                      onSave={(v) => {
                        updateUser(user.id, { display_name: v });
                        setEditingId(null);
                      }}
                      onCancel={() => setEditingId(null)}
                    />
                  ) : (
                    <span
                      onClick={() => setEditingId(user.id)}
                      className="cursor-pointer hover:text-purple-600"
                      title="Klik om te bewerken"
                    >
                      {user.display_name || "-"}
                    </span>
                  )}
                </Td>
                <Td>{user.email || "-"}</Td>
                <Td>
                  <select
                    value={user.role}
                    onChange={(e) => handleRoleChange(user, e.target.value)}
                    disabled={user.id === currentUser?.id}
                    className="text-xs rounded border-gray-300 bg-transparent disabled:opacity-50"
                  >
                    <option value="user">Gebruiker</option>
                    <option value="admin">Admin</option>
                  </select>
                </Td>
                <Td>{user.tenant || "-"}</Td>
                <Td>
                  <button
                    onClick={() => handleToggleActive(user)}
                    disabled={user.id === currentUser?.id}
                    className={`rounded-full px-2 py-0.5 text-xs font-medium disabled:cursor-not-allowed ${
                      user.is_active
                        ? "bg-green-100 text-green-700"
                        : "bg-red-100 text-red-700"
                    }`}
                  >
                    {user.is_active ? "Actief" : "Inactief"}
                  </button>
                </Td>
                <Td>
                  <div className="flex items-center gap-1">
                    <button
                      onClick={() => { setResetId(user.id); setNewPassword(""); }}
                      className="rounded px-2 py-1 text-xs text-gray-600 hover:bg-gray-100"
                      title="Wachtwoord resetten"
                    >
                      Reset ww
                    </button>
                    {user.id !== currentUser?.id && (
                      <button
                        onClick={() => setConfirmDelete(user.id)}
                        className="rounded px-2 py-1 text-xs text-red-600 hover:bg-red-50"
                        title="Verwijderen"
                      >
                        Verwijder
                      </button>
                    )}
                  </div>
                </Td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Reset password dialog */}
      {resetId && (
        <Dialog
          title="Wachtwoord resetten"
          onClose={() => setResetId(null)}
        >
          <Input
            label="Nieuw wachtwoord"
            type="password"
            value={newPassword}
            onChange={setNewPassword}
          />
          <div className="mt-4 flex justify-end gap-2">
            <button
              onClick={() => setResetId(null)}
              className="rounded-md border border-gray-300 px-4 py-2 text-sm text-gray-700 hover:bg-gray-50"
            >
              Annuleren
            </button>
            <button
              onClick={handleResetPassword}
              disabled={newPassword.length < 6}
              className="rounded-md bg-purple-600 px-4 py-2 text-sm font-medium text-white hover:bg-purple-700 disabled:opacity-40 disabled:cursor-not-allowed"
            >
              Resetten
            </button>
          </div>
        </Dialog>
      )}

      {/* Confirm delete dialog */}
      {confirmDelete && (
        <Dialog
          title="Gebruiker verwijderen"
          onClose={() => setConfirmDelete(null)}
        >
          <p className="text-sm text-gray-600">
            Weet je zeker dat je deze gebruiker wilt verwijderen? Dit kan niet ongedaan worden.
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

// ---------- Shared sub-components ----------

function Th({ children }: { children: React.ReactNode }) {
  return (
    <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
      {children}
    </th>
  );
}

function Td({ children, className = "" }: { children: React.ReactNode; className?: string }) {
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
  type = "text",
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  type?: string;
}) {
  return (
    <label className="block">
      <span className="text-xs font-medium text-gray-600">{label}</span>
      <input
        type={type}
        value={value}
        onChange={(e) => onChange(e.target.value)}
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
          <option key={o.value} value={o.value}>{o.label}</option>
        ))}
      </select>
    </label>
  );
}

function InlineEdit({
  value,
  onSave,
  onCancel,
}: {
  value: string;
  onSave: (v: string) => void;
  onCancel: () => void;
}) {
  const [text, setText] = useState(value);
  return (
    <input
      autoFocus
      value={text}
      onChange={(e) => setText(e.target.value)}
      onBlur={() => onSave(text)}
      onKeyDown={(e) => {
        if (e.key === "Enter") onSave(text);
        if (e.key === "Escape") onCancel();
      }}
      className="w-full rounded border border-purple-300 px-2 py-0.5 text-sm focus:outline-none focus:ring-1 focus:ring-purple-500"
    />
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
        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
      </svg>
      {label}
    </div>
  );
}
