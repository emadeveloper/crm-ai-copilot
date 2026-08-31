import type { Lead } from "../../api/leads";
import { useLeads } from "./hooks";

function scoreBand(lead: Lead): string {
  return lead.score ? lead.score.band : "—";
}

export function QueueView({ onSelect }: { onSelect: (id: string) => void }) {
  const { data: leads, isPending, isError } = useLeads();

  if (isPending) return <p>Loading leads…</p>;
  if (isError) return <p role="alert">Could not load leads.</p>;
  if (leads.length === 0) return <p>No leads yet. Add one to get started.</p>;

  return (
    <table>
      <thead>
        <tr>
          <th>Name</th>
          <th>Company</th>
          <th>Status</th>
          <th>Score</th>
        </tr>
      </thead>
      <tbody>
        {leads.map((lead) => (
          <tr key={lead.id} onClick={() => onSelect(lead.id)} style={{ cursor: "pointer" }}>
            <td>{lead.contact.name}</td>
            <td>{lead.contact.company ?? "—"}</td>
            <td>{lead.status}</td>
            <td>{scoreBand(lead)}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
