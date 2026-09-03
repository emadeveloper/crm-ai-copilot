type Style = { text: string; border: string; dot: string };

// Literal class strings so Tailwind's scanner keeps them.
const STYLES: Record<string, Style> = {
  received: { text: "text-st-received", border: "border-st-received/35", dot: "bg-st-received" },
  enriching: { text: "text-st-enriching", border: "border-st-enriching/35", dot: "bg-st-enriching" },
  qualified: { text: "text-st-qualified", border: "border-st-qualified/35", dot: "bg-st-qualified" },
  syncing: { text: "text-st-syncing", border: "border-st-syncing/35", dot: "bg-st-syncing" },
  synced: { text: "text-st-synced", border: "border-st-synced/35", dot: "bg-st-synced" },
  failed: { text: "text-st-failed", border: "border-st-failed/35", dot: "bg-st-failed" },
};

const FALLBACK: Style = {
  text: "text-st-received",
  border: "border-st-received/35",
  dot: "bg-st-received",
};

export function StatusBadge({ status }: { status: string }) {
  const s = STYLES[status] ?? FALLBACK;
  return (
    <span
      data-status={status}
      className={`inline-flex items-center gap-1.5 rounded-[2px] border px-2 py-[3px] font-mono text-[10px] uppercase tracking-[0.1em] ${s.text} ${s.border}`}
    >
      <span className={`size-1 rounded-full ${s.dot}`} />
      {status}
    </span>
  );
}
