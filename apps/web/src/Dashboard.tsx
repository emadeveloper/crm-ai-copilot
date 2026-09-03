import { useState } from "react";
import { AddLeadForm } from "./features/leads/AddLeadForm";
import { LeadDetail } from "./features/leads/LeadDetail";
import { QueueView } from "./features/leads/QueueView";

export function Dashboard() {
  const [selected, setSelected] = useState<string | null>(null);
  const [adding, setAdding] = useState(false);

  function handleCreated(id: string) {
    setSelected(id);
    setAdding(false);
  }

  return (
    <main className="flex h-full flex-col overflow-hidden bg-bg text-ink">
      <header className="flex min-h-14 flex-shrink-0 flex-wrap items-center gap-x-5 gap-y-2 border-b border-line px-[22px] py-2">
        <div className="flex items-center gap-2.5">
          <svg width="18" height="18" viewBox="0 0 18 18" fill="none" aria-hidden="true">
            <path d="M2 13L9 2l7 11H2z" fill="#c9f24a" />
            <rect x="7" y="9" width="4" height="4" fill="#0a0b0d" />
          </svg>
          <h1 className="font-mono text-xs font-semibold tracking-[0.16em] text-ink">
            CRM AI COPILOT
          </h1>
        </div>
        <p className="text-[13px] text-muted max-sm:w-full">
          AI qualifies every inbound lead and syncs it to HubSpot.
        </p>
        <div className="ml-auto flex items-center gap-4">
          <span className="flex items-center gap-1.5 font-mono text-[10px] uppercase tracking-[0.12em] text-dim">
            <span className="size-[5px] rounded-full bg-st-synced shadow-[0_0_6px_#54d98a]" />
            worker · live
          </span>
          <button
            type="button"
            onClick={() => setAdding((open) => !open)}
            aria-expanded={adding}
            className="flex items-center gap-1.5 rounded-[3px] border border-accent/40 px-3 py-1.5 font-mono text-[10px] uppercase tracking-[0.14em] text-accent transition-colors hover:bg-accent/10 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent"
          >
            {adding ? "Close" : "+ Add lead"}
          </button>
        </div>
      </header>

      <div className="grid min-h-0 flex-1 grid-cols-1 lg:grid-cols-[minmax(0,1fr)_440px]">
        <section
          aria-label="Lead queue"
          className="flex min-w-0 flex-col overflow-hidden border-line lg:border-r"
        >
          {adding && (
            <div className="m-4 flex-shrink-0 rounded-md border border-line bg-panel p-5 shadow-[0_24px_60px_-20px_#000]">
              <h2 className="mb-4 font-mono text-[11px] uppercase tracking-[0.16em] text-muted">
                New lead
              </h2>
              <AddLeadForm onCreated={handleCreated} />
            </div>
          )}
          <div className="flex flex-shrink-0 items-baseline gap-3 px-[22px] pb-3 pt-4">
            <h2 className="font-mono text-[11px] uppercase tracking-[0.16em] text-muted">
              Lead queue
            </h2>
            <span className="font-mono text-[11px] text-dim">newest first</span>
          </div>
          <div className="min-h-0 flex-1 overflow-auto px-3 pb-4">
            <QueueView onSelect={setSelected} selectedId={selected} />
          </div>
        </section>

        {selected ? (
          <section
            aria-label="Lead detail"
            className="flex min-w-0 flex-col overflow-hidden"
          >
            <div className="flex flex-shrink-0 justify-end px-[22px] pt-4">
              <button
                type="button"
                onClick={() => setSelected(null)}
                className="font-mono text-[10px] uppercase tracking-[0.14em] text-dim transition-colors hover:text-ink focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent"
              >
                Close
              </button>
            </div>
            <div className="min-h-0 flex-1 overflow-auto">
              <LeadDetail leadId={selected} />
            </div>
          </section>
        ) : (
          <aside className="hidden items-center justify-center p-[22px] text-center lg:flex">
            <p className="font-mono text-[11px] leading-loose tracking-[0.1em] text-dim">
              SELECT A LEAD
              <br />
              TO SEE ITS AI ANALYSIS
            </p>
          </aside>
        )}
      </div>
    </main>
  );
}
