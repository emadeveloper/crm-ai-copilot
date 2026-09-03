import { ScoreMeter } from "../../components/ScoreMeter";
import { StatusBadge } from "../../components/StatusBadge";
import { useLeads } from "./hooks";

const HEAD_CLASS =
  "border-b border-line px-2.5 py-2 text-left font-mono text-[10px] font-medium uppercase tracking-[0.14em] text-dim";
const CELL_CLASS = "border-b border-line-soft px-2.5 py-3 align-middle";

export function QueueView({
  onSelect,
  selectedId,
}: {
  onSelect: (id: string) => void;
  selectedId?: string | null;
}) {
  const { data: leads, isPending, isError } = useLeads();

  if (isPending)
    return <p className="px-2.5 py-3 font-mono text-[11px] text-dim">Loading leads…</p>;
  if (isError)
    return (
      <p role="alert" className="px-2.5 py-3 font-mono text-[11px] text-st-failed">
        Could not load leads.
      </p>
    );
  if (leads.length === 0)
    return (
      <p className="px-2.5 py-3 font-mono text-[11px] text-dim">
        No leads yet. Add one to get started.
      </p>
    );

  return (
    <table className="w-full border-collapse">
      <thead>
        <tr>
          <th className={HEAD_CLASS}>Name</th>
          <th className={HEAD_CLASS}>Company</th>
          <th className={HEAD_CLASS}>Status</th>
          <th className={`${HEAD_CLASS} w-[150px]`}>Score</th>
        </tr>
      </thead>
      <tbody>
        {leads.map((lead, i) => {
          const selected = lead.id === selectedId;
          return (
            <tr
              key={lead.id}
              onClick={() => onSelect(lead.id)}
              data-selected={selected || undefined}
              className={`cursor-pointer transition-colors hover:bg-raised ${
                selected
                  ? "bg-[#c9f24a0d] shadow-[inset_2px_0_0_#c9f24a]"
                  : ""
              }`}
              style={{ animation: "rise 0.4s ease both", animationDelay: `${i * 35}ms` }}
            >
              <td className={`${CELL_CLASS} text-sm text-ink ${selected ? "font-medium" : ""}`}>
                {lead.contact.name}
              </td>
              <td className={`${CELL_CLASS} text-[13px] text-muted`}>
                {lead.contact.company ?? "—"}
              </td>
              <td className={CELL_CLASS}>
                <StatusBadge status={lead.status} />
              </td>
              <td className={CELL_CLASS}>
                {lead.score ? (
                  <ScoreMeter value={lead.score.value} band={lead.score.band} size="sm" />
                ) : (
                  <span className="font-mono text-xs text-dim">—</span>
                )}
              </td>
            </tr>
          );
        })}
      </tbody>
    </table>
  );
}
