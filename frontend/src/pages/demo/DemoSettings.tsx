import ThemeToggle from "../../components/ThemeToggle";
import DemoPageShell from "../../components/demo/DemoPageShell";
import DemoUserSwitcher from "../../components/demo/DemoUserSwitcher";

export default function DemoSettings() {
  return (
    <DemoPageShell title="Settings" subtitle="Preferences for your account and learning experience">
      <div className="space-y-4">
        <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-900">
          <DemoUserSwitcher />
        </section>

        <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-900">
          <h3 className="text-sm font-semibold text-slate-900 dark:text-slate-50">Appearance</h3>
          <div className="mt-3 flex items-center justify-between">
            <span className="text-sm text-slate-600 dark:text-slate-300">Theme</span>
            <ThemeToggle />
          </div>
        </section>

        <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-900">
          <h3 className="text-sm font-semibold text-slate-900 dark:text-slate-50">Notifications</h3>
          <label className="mt-3 flex items-center justify-between text-sm text-slate-600 dark:text-slate-300">
            Email reminders for due dates
            <input type="checkbox" defaultChecked className="h-4 w-4 rounded border-slate-300 text-brand-600" />
          </label>
          <label className="mt-2 flex items-center justify-between text-sm text-slate-600 dark:text-slate-300">
            Announcement alerts
            <input type="checkbox" defaultChecked className="h-4 w-4 rounded border-slate-300 text-brand-600" />
          </label>
        </section>

        <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-900">
          <h3 className="text-sm font-semibold text-slate-900 dark:text-slate-50">Password & security</h3>
          <p className="mt-2 text-sm text-slate-600 dark:text-slate-300">
            Change your password from the login screen using Forgot password, or ask the support assistant for a
            guided reset.
          </p>
          <button
            type="button"
            className="mt-4 rounded-xl border border-slate-200 px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50 dark:border-slate-700 dark:text-slate-200 dark:hover:bg-slate-800"
          >
            Update password (demo)
          </button>
        </section>

        <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-900">
          <h3 className="text-sm font-semibold text-slate-900 dark:text-slate-50">Account preferences</h3>
          <p className="mt-2 text-sm text-slate-600 dark:text-slate-300">Language: English (US)</p>
          <p className="text-sm text-slate-600 dark:text-slate-300">Time zone: Auto-detect</p>
        </section>
      </div>
    </DemoPageShell>
  );
}
