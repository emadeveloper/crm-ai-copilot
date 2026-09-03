import { type FormEvent, useState } from "react";
import { LeadValidationError } from "../../api/leads";
import { useCreateLead } from "./hooks";

const EMPTY = { name: "", email: "", company: "", role: "", message: "" };

const LABEL_TEXT = "font-mono text-[10px] uppercase tracking-[0.1em] text-dim";
const FIELD =
  "rounded border border-line bg-raised px-[11px] py-[9px] font-sans text-[13px] text-ink outline-none transition-shadow focus:border-accent focus:shadow-[0_0_0_3px_#c9f24a22]";

export function AddLeadForm({ onCreated }: { onCreated: (id: string) => void }) {
  const [fields, setFields] = useState(EMPTY);
  const [error, setError] = useState<string | null>(null);
  const createLead = useCreateLead();

  function update(key: keyof typeof EMPTY) {
    return (event: { target: { value: string } }) =>
      setFields((prev) => ({ ...prev, [key]: event.target.value }));
  }

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    try {
      const created = await createLead.mutateAsync({
        source: "dashboard",
        contact: {
          name: fields.name,
          email: fields.email,
          company: fields.company || null,
          role: fields.role || null,
          message: fields.message || null,
        },
      });
      setFields(EMPTY);
      onCreated(created.id);
    } catch (err) {
      setError(
        err instanceof LeadValidationError
          ? "Please check the form and try again."
          : "Something went wrong. Please try again.",
      );
    }
  }

  return (
    <form onSubmit={handleSubmit} aria-label="Add lead" className="flex flex-col gap-3.5">
      {error && (
        <p
          role="alert"
          className="rounded border border-st-failed/40 bg-st-failed/10 px-3 py-2 font-mono text-[11px] text-st-failed"
        >
          {error}
        </p>
      )}
      <div className="grid gap-3.5 sm:grid-cols-2">
        <label className="flex flex-col gap-1.5">
          <span className={LABEL_TEXT}>Name</span>
          <input value={fields.name} onChange={update("name")} required className={FIELD} />
        </label>
        <label className="flex flex-col gap-1.5">
          <span className={LABEL_TEXT}>Email</span>
          <input
            type="email"
            value={fields.email}
            onChange={update("email")}
            required
            className={FIELD}
          />
        </label>
        <label className="flex flex-col gap-1.5">
          <span className={LABEL_TEXT}>Company</span>
          <input value={fields.company} onChange={update("company")} className={FIELD} />
        </label>
        <label className="flex flex-col gap-1.5">
          <span className={LABEL_TEXT}>Role</span>
          <input value={fields.role} onChange={update("role")} className={FIELD} />
        </label>
        <label className="flex flex-col gap-1.5 sm:col-span-2">
          <span className={LABEL_TEXT}>Message</span>
          <textarea
            value={fields.message}
            onChange={update("message")}
            className={`${FIELD} max-h-[200px] min-h-[58px] resize-y`}
          />
        </label>
      </div>
      <div className="flex gap-2.5">
        <button
          type="submit"
          disabled={createLead.isPending}
          className="rounded border-0 bg-accent px-[18px] py-[9px] font-mono text-[10px] uppercase tracking-[0.14em] text-bg transition-opacity hover:opacity-90 disabled:opacity-50"
        >
          Add lead
        </button>
      </div>
    </form>
  );
}
