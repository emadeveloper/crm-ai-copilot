import { useState } from "react";
import { AddLeadForm } from "./features/leads/AddLeadForm";
import { LeadDetail } from "./features/leads/LeadDetail";
import { QueueView } from "./features/leads/QueueView";

export function Dashboard() {
  const [selected, setSelected] = useState<string | null>(null);

  return (
    <main>
      <h1>CRM AI Copilot</h1>
      <p>AI qualifies each inbound lead and syncs it to HubSpot.</p>

      <section aria-label="Add a lead">
        <h2>Add a lead</h2>
        <AddLeadForm onCreated={setSelected} />
      </section>

      <section aria-label="Lead queue">
        <h2>Lead queue</h2>
        <QueueView onSelect={setSelected} />
      </section>

      {selected && (
        <section aria-label="Lead detail">
          <button type="button" onClick={() => setSelected(null)}>
            Close
          </button>
          <LeadDetail leadId={selected} />
        </section>
      )}
    </main>
  );
}
