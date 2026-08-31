import { useLead } from "./hooks";

const HUBSPOT_CONTACT_URL = "https://app.hubspot.com/contacts/contact/";

export function LeadDetail({ leadId }: { leadId: string }) {
  const { data: lead, isPending, isError } = useLead(leadId);

  if (isPending) return <p>Loading lead…</p>;
  if (isError) return <p role="alert">Lead not found.</p>;

  return (
    <article>
      <header>
        <h2>{lead.contact.name}</h2>
        <p>
          {lead.contact.company ?? "—"} · {lead.contact.email} · <strong>{lead.status}</strong>
        </p>
        {lead.contact.message && <blockquote>{lead.contact.message}</blockquote>}
      </header>

      {lead.score ? (
        <>
          <section aria-label="AI qualification">
            <h3>
              Score: {lead.score.value}/100 <span>({lead.score.band})</span>
            </h3>
            <p>{lead.score.rationale}</p>
          </section>

          {lead.enrichment && (
            <section aria-label="Enrichment">
              <dl>
                <dt>Industry</dt>
                <dd>{lead.enrichment.industry ?? "—"}</dd>
                <dt>Company size</dt>
                <dd>{lead.enrichment.company_size_band ?? "—"}</dd>
                <dt>Seniority</dt>
                <dd>{lead.enrichment.seniority ?? "—"}</dd>
                <dt>Intent signals</dt>
                <dd>{lead.enrichment.intent_signals.join(", ") || "—"}</dd>
              </dl>
            </section>
          )}

          {lead.reply_draft && (
            <section aria-label="Suggested reply">
              <h3>{lead.reply_draft.subject}</h3>
              <p>{lead.reply_draft.body}</p>
            </section>
          )}
        </>
      ) : (
        <p>Pending enrichment — this lead has not been scored yet.</p>
      )}

      {lead.sync_state && (
        <footer>
          <p>CRM sync: {lead.sync_state.status}</p>
          {lead.sync_state.crm_contact_id && (
            <a
              href={`${HUBSPOT_CONTACT_URL}${lead.sync_state.crm_contact_id}`}
              target="_blank"
              rel="noreferrer"
            >
              View in HubSpot
            </a>
          )}
          {lead.sync_state.failure_reason && (
            <p role="alert">Sync failed: {lead.sync_state.failure_reason}</p>
          )}
        </footer>
      )}
    </article>
  );
}
