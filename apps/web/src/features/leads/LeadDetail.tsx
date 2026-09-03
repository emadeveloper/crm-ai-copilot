import { ScoreMeter } from "../../components/ScoreMeter";
import { StatusBadge } from "../../components/StatusBadge";
import { useLead } from "./hooks";

const HUBSPOT_CONTACT_URL = "https://app.hubspot.com/contacts/contact/";

const SECTION_LABEL = "font-mono text-[10px] uppercase tracking-[0.16em] text-dim";
const FIELD_LABEL = "font-mono text-[10px] uppercase tracking-[0.08em] text-dim";

export function LeadDetail({ leadId }: { leadId: string }) {
  const { data: lead, isPending, isError } = useLead(leadId);

  if (isPending)
    return <p className="p-[22px] font-mono text-[11px] text-dim">Loading lead…</p>;
  if (isError)
    return (
      <p role="alert" className="p-[22px] font-mono text-[11px] text-st-failed">
        Lead not found.
      </p>
    );

  return (
    <article className="flex flex-col gap-[22px] p-[22px] pb-7">
      <header className="flex flex-col gap-2.5">
        <div className="flex items-center justify-between gap-3">
          <h2 className="text-xl font-semibold tracking-[-0.01em] text-ink">{lead.contact.name}</h2>
          <StatusBadge status={lead.status} />
        </div>
        <p className="break-words font-mono text-[11px] tracking-[0.02em] text-muted">
          {lead.contact.company ?? "—"} · {lead.contact.email}
          {lead.contact.role ? ` · ${lead.contact.role}` : ""}
        </p>
        {lead.contact.message && (
          <blockquote className="border-l-2 border-accent py-1 pl-3 text-[13px] leading-relaxed break-words text-muted">
            {lead.contact.message}
          </blockquote>
        )}
      </header>

      {lead.score ? (
        <>
          <section aria-label="AI qualification" className="flex flex-col gap-3">
            <div className={SECTION_LABEL}>AI qualification</div>
            <ScoreMeter value={lead.score.value} band={lead.score.band} size="lg" />
            <p className="text-[13px] leading-relaxed text-[#b7bcc5]">{lead.score.rationale}</p>
          </section>

          {lead.enrichment && (
            <section aria-label="Enrichment" className="flex flex-col gap-3">
              <div className={SECTION_LABEL}>Enrichment</div>
              <dl className="grid grid-cols-[110px_1fr] gap-x-3.5 gap-y-2 text-[13px] text-ink">
                <dt className={`self-center ${FIELD_LABEL}`}>Industry</dt>
                <dd>{lead.enrichment.industry ?? "—"}</dd>
                <dt className={`self-center ${FIELD_LABEL}`}>Company size</dt>
                <dd>{lead.enrichment.company_size_band ?? "—"}</dd>
                <dt className={`self-center ${FIELD_LABEL}`}>Seniority</dt>
                <dd>{lead.enrichment.seniority ?? "—"}</dd>
                <dt className={`pt-1 ${FIELD_LABEL}`}>Intent signals</dt>
                <dd className="flex flex-wrap gap-1.5">
                  {lead.enrichment.intent_signals.length > 0
                    ? lead.enrichment.intent_signals.map((signal) => (
                        <span
                          key={signal}
                          className="rounded-[2px] border border-line bg-raised px-2 py-[3px] text-[11px] text-[#b7bcc5]"
                        >
                          {signal}
                        </span>
                      ))
                    : "—"}
                </dd>
              </dl>
            </section>
          )}

          {lead.reply_draft && (
            <section aria-label="Suggested reply" className="flex flex-col gap-2.5">
              <div className={SECTION_LABEL}>Suggested reply</div>
              <div className="flex flex-col gap-2 rounded border border-line bg-panel px-4 py-3.5">
                <h3 className="text-sm font-semibold break-words text-ink">{lead.reply_draft.subject}</h3>
                <p className="text-[13px] leading-relaxed break-words text-muted">{lead.reply_draft.body}</p>
              </div>
            </section>
          )}
        </>
      ) : (
        <p className="font-mono text-[11px] text-dim">
          Pending enrichment — this lead has not been scored yet.
        </p>
      )}

      {lead.sync_state && (
        <footer className="flex flex-wrap items-center gap-3 border-t border-line pt-3.5">
          <span className={SECTION_LABEL}>CRM sync</span>
          <StatusBadge status={lead.sync_state.status} />
          {lead.sync_state.crm_contact_id && (
            <a
              href={`${HUBSPOT_CONTACT_URL}${lead.sync_state.crm_contact_id}`}
              target="_blank"
              rel="noreferrer"
              className="ml-auto font-mono text-[11px] tracking-[0.06em] text-accent hover:underline"
            >
              View in HubSpot
            </a>
          )}
          {lead.sync_state.failure_reason && (
            <p role="alert" className="w-full font-mono text-[11px] text-st-failed">
              Sync failed: {lead.sync_state.failure_reason}
            </p>
          )}
        </footer>
      )}
    </article>
  );
}
