import { useChat } from "../../context/ChatContext";
import DemoPageShell from "../../components/demo/DemoPageShell";

export default function DemoHelp() {
  const { setOpen, setTicketOpen } = useChat();

  const contactSupport = () => {
    setOpen(true);
    setTicketOpen(true);
  };

  return (
    <DemoPageShell title="Help" subtitle="We're here if you get stuck">
      <div className="grid gap-4 md:grid-cols-2">
        <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-900">
          <h3 className="text-sm font-semibold text-slate-900 dark:text-slate-50">Contact support</h3>
          <p className="mt-2 text-sm text-slate-600 dark:text-slate-300">
            Email:{" "}
            <a href="mailto:support@smarted.test" className="font-medium text-brand-600 hover:underline">
              support@smarted.test
            </a>
          </p>
          <p className="mt-2 text-sm text-slate-600 dark:text-slate-300">Customer care hours: Mon–Fri, 9am–6pm</p>
          <button
            type="button"
            onClick={contactSupport}
            className="mt-4 rounded-xl bg-brand-600 px-4 py-2 text-sm font-semibold text-white hover:bg-brand-700"
          >
            Contact Support
          </button>
          <p className="mt-2 text-xs text-slate-500">Opens the in-app support assistant to create a ticket.</p>
        </section>

        <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-900">
          <h3 className="text-sm font-semibold text-slate-900 dark:text-slate-50">FAQ</h3>
          <ul className="mt-3 space-y-2 text-sm text-slate-600 dark:text-slate-300">
            <li>· How do I enroll in a new course?</li>
            <li>· Where are my assignment due dates?</li>
            <li>· When do I receive certificates?</li>
          </ul>
          <p className="mt-4 text-xs text-slate-500">Use the floating assistant for guided answers.</p>
        </section>
      </div>
    </DemoPageShell>
  );
}
