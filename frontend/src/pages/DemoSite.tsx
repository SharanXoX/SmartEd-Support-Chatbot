import { Link } from "react-router-dom";
import FloatingChat from "../components/FloatingChat";
import ThemeToggle from "../components/ThemeToggle";

export default function DemoSite() {
  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-50 to-white dark:from-slate-950 dark:to-slate-900">
      <header className="mx-auto flex max-w-6xl items-center justify-between px-6 py-6">
        <div className="text-sm font-semibold text-slate-900 dark:text-slate-50">SmartEd Demo Site</div>
        <div className="flex items-center gap-3">
          <ThemeToggle />
          <Link to="/admin" className="text-sm font-medium text-brand-600 hover:underline">
            Admin
          </Link>
        </div>
      </header>

      <main className="mx-auto grid max-w-6xl gap-10 px-6 pb-24 pt-10 md:grid-cols-2 md:items-center">
        <div>
          <div className="inline-flex items-center gap-2 rounded-full bg-brand-600/10 px-3 py-1 text-xs font-semibold text-brand-700 ring-1 ring-brand-600/20 dark:text-brand-300">
            Visual-first AI support
          </div>
          <h1 className="mt-5 text-4xl font-semibold tracking-tight text-slate-900 dark:text-slate-50 md:text-5xl">
            Troubleshooting that shows, not just tells.
          </h1>
          <p className="mt-4 text-base leading-relaxed text-slate-600 dark:text-slate-300">
            Ask natural-language questions and get guided flows with screenshots, highlights, clarifying questions,
            citations from your knowledge base, and seamless escalation when confidence is low.
          </p>

          <div className="mt-8 grid gap-3 text-sm text-slate-700 dark:text-slate-200">
            <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm dark:border-slate-800 dark:bg-slate-950">
              <div className="font-semibold">Try asking</div>
              <ul className="mt-2 list-disc space-y-1 pl-5 text-slate-600 dark:text-slate-300">
                <li>How do I reset my password?</li>
                <li>Payment failed — what should I check?</li>
                <li>Where do I upload documents?</li>
              </ul>
            </div>
          </div>
        </div>

        <div className="rounded-3xl border border-slate-200 bg-white p-6 shadow-xl dark:border-slate-800 dark:bg-slate-950">
          <div className="text-sm font-semibold text-slate-900 dark:text-slate-50">Live preview</div>
          <p className="mt-2 text-sm text-slate-600 dark:text-slate-300">
            Open the floating widget — it connects to your FastAPI backend (proxied in dev via Vite).
          </p>
          <div className="mt-6 grid gap-3">
            <div className="h-28 rounded-2xl bg-slate-100 dark:bg-slate-900" />
            <div className="h-28 rounded-2xl bg-slate-100 dark:bg-slate-900" />
            <div className="h-28 rounded-2xl bg-slate-100 dark:bg-slate-900" />
          </div>
        </div>
      </main>

      <FloatingChat />
    </div>
  );
}
