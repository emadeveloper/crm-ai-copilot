import { type FormEvent, useState } from "react";
import { LeadValidationError } from "../../api/leads";
import { useCreateLead } from "./hooks";

const EMPTY = { name: "", email: "", company: "", role: "", message: "" };

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
    <form onSubmit={handleSubmit} aria-label="Add lead">
      {error && <p role="alert">{error}</p>}
      <label>
        Name
        <input value={fields.name} onChange={update("name")} required />
      </label>
      <label>
        Email
        <input type="email" value={fields.email} onChange={update("email")} required />
      </label>
      <label>
        Company
        <input value={fields.company} onChange={update("company")} />
      </label>
      <label>
        Role
        <input value={fields.role} onChange={update("role")} />
      </label>
      <label>
        Message
        <textarea value={fields.message} onChange={update("message")} />
      </label>
      <button type="submit" disabled={createLead.isPending}>
        Add lead
      </button>
    </form>
  );
}
