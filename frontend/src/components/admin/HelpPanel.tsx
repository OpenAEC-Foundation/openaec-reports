export function HelpPanel() {
  return (
    <div
      className="rounded-lg border border-gray-200 overflow-hidden"
      style={{ height: "calc(100vh - 200px)" }}
    >
      <iframe
        src="/api/docs/architecture"
        title="Architecture & Tenant Guide"
        className="w-full h-full border-0"
      />
    </div>
  );
}
