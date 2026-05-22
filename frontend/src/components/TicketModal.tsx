import { useState } from "react";
import { api } from "../api/client";

type Props = {
  open: boolean;
  onClose: () => void;
  sessionKey: string;
  defaultName?: string;
  defaultEmail?: string;
};

export default function TicketModal({ open, onClose, sessionKey, defaultName = "", defaultEmail = "" }: Props) {
  const [name, setName] = useState(defaultName);
  const [email, setEmail] = useState(defaultEmail);
  const [issue, setIssue] = useState("");
  const [busy, setBusy] = useState(false);
  const [done, setDone] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  if (!open) return null;

  async function submit() {
    setBusy(true);
    setError(null);
    try {
      const resp = await api.post<{ id: string; message: string }>("/demo/support/ticket", {
        name: name.trim(),
        email: email.trim(),
        issue: issue.trim(),
        session_key: sessionKey,
      });
      setDone(resp.data.message ?? "Ticket submitted. We'll email you soon.");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not submit ticket");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div
      className="fixed inset-0 z-[60] flex items-center justify-center bg-black/50 p-4 backdrop-blur-sm"
      role="dialog"
      aria-modal="true"
    >
      <div className="w-full max-w-md rounded-2xl border border-slate-200 bg-white p-5 shadow-2xl dark:border-slate-800 dark:bg-slate-950">
        <div className="flex items-start justify-between gap-2">
          <div>
            <h3 className="text-base font-semibold text-slate-900 dark:text-slate-50">Contact support</h3>
            <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
              A human specialist will follow up by email.
            </p>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="rounded-lg px-2 py-1 text-sm text-slate-500 hover:bg-slate-100 dark:hover:bg-slate-900"
          >
            ✕
          </button>
        </div>

        {done ? (
          <p className="mt-4 rounded-lg bg-emerald-50 px-3 py-3 text-sm text-emerald-900 dark:bg-emerald-950/40 dark:text-emerald-100">
            {done}
          </p>
        ) : (
          <div className="mt-4 space-y-3">
            <label className="block text-xs font-medium text-slate-600 dark:text-slate-300">
              Name
              <input
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="mt-1 w-full rounded-xl border border-slate-200 px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-900"
              />
            </label>
            <label className="block text-xs font-medium text-slate-600 dark:text-slate-300">
              Email
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="mt-1 w-full rounded-xl border border-slate-200 px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-900"
              />
            </label>
            <label className="block text-xs font-medium text-slate-600 dark:text-slate-300">
              Describe your issue
              <textarea
                value={issue}
                onChange={(e) => setIssue(e.target.value)}
                rows={4}
                className="mt-1 w-full rounded-xl border border-slate-200 px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-900"
              />
            </label>
            {error ? <p className="text-xs text-red-600 dark:text-red-400">{error}</p> : null}
            <button
              type="button"
              disabled={busy || !name.trim() || !email.trim() || issue.trim().length < 5}
              onClick={() => void submit()}
              className="w-full rounded-xl bg-brand-600 py-2.5 text-sm font-semibold text-white disabled:opacity-50"
            >
              {busy ? "Sending…" : "Submit ticket"}
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
