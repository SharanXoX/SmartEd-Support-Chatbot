import { useOutletContext } from "react-router-dom";
import DemoPageShell from "../../components/demo/DemoPageShell";
import DemoUserSwitcher from "../../components/demo/DemoUserSwitcher";
import type { LmsStudentState } from "../../services/mockApi";

export default function DemoProfile() {
  const { student } = useOutletContext<{ student: LmsStudentState }>();
  const avgProgress = Math.round(
    student.courses.reduce((s, c) => s + c.progress_pct, 0) / Math.max(student.courses.length, 1),
  );

  return (
    <DemoPageShell title="Profile" subtitle="Your learner identity on SmartEd Learn">
      <div className="grid gap-6 lg:grid-cols-3">
        <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-slate-900 lg:col-span-1">
          <div className="mx-auto flex h-24 w-24 items-center justify-center rounded-full bg-brand-600 text-3xl font-bold text-white">
            {student.name.charAt(0)}
          </div>
          <h2 className="mt-4 text-center text-lg font-semibold text-slate-900 dark:text-slate-50">
            {student.name}
          </h2>
          <p className="text-center text-sm text-slate-500">{student.email}</p>
          <p className="mt-2 text-center text-xs text-slate-400 capitalize">
            {student.role}
            {student.profile_type ? ` · ${student.profile_type}` : ""}
          </p>
        </section>

        <section className="space-y-4 lg:col-span-2">
          <div className="grid gap-4 sm:grid-cols-3">
            <div className="rounded-xl border border-slate-200 bg-slate-50 p-4 dark:border-slate-800 dark:bg-slate-950">
              <div className="text-xs text-slate-500">Enrolled courses</div>
              <div className="text-2xl font-bold text-slate-900 dark:text-slate-50">{student.courses.length}</div>
            </div>
            <div className="rounded-xl border border-slate-200 bg-slate-50 p-4 dark:border-slate-800 dark:bg-slate-950">
              <div className="text-xs text-slate-500">Avg. progress</div>
              <div className="text-2xl font-bold text-brand-600">{avgProgress}%</div>
            </div>
            <div className="rounded-xl border border-slate-200 bg-slate-50 p-4 dark:border-slate-800 dark:bg-slate-950">
              <div className="text-xs text-slate-500">Certificates</div>
              <div className="text-2xl font-bold text-slate-900 dark:text-slate-50">
                {student.certificates.length}
              </div>
            </div>
          </div>

          {student.recent_activity.length > 0 ? (
            <div className="rounded-2xl border border-slate-200 bg-white p-5 dark:border-slate-800 dark:bg-slate-900">
              <h3 className="text-sm font-semibold text-slate-900 dark:text-slate-50">Recent activity</h3>
              <ul className="mt-3 space-y-2 text-sm text-slate-600 dark:text-slate-300">
                {student.recent_activity.map((a) => (
                  <li key={a.id}>
                    {a.text} <span className="text-xs text-slate-400">· {a.at}</span>
                  </li>
                ))}
              </ul>
            </div>
          ) : null}

          <div className="rounded-2xl border border-slate-200 bg-white p-5 dark:border-slate-800 dark:bg-slate-900">
            <DemoUserSwitcher />
          </div>

          <div className="rounded-2xl border border-slate-200 bg-white p-5 dark:border-slate-800 dark:bg-slate-900">
            <h3 className="text-sm font-semibold text-slate-900 dark:text-slate-50">Account details</h3>
            <dl className="mt-4 space-y-3 text-sm">
              <div className="flex justify-between gap-4">
                <dt className="text-slate-500">Display name</dt>
                <dd className="font-medium text-slate-900 dark:text-slate-100">{student.name}</dd>
              </div>
              <div className="flex justify-between gap-4">
                <dt className="text-slate-500">Email</dt>
                <dd className="font-medium text-slate-900 dark:text-slate-100">{student.email}</dd>
              </div>
              <div className="flex justify-between gap-4">
                <dt className="text-slate-500">Student ID</dt>
                <dd className="font-mono text-xs text-slate-700 dark:text-slate-300">{student.student_id}</dd>
              </div>
            </dl>
          </div>
        </section>
      </div>
    </DemoPageShell>
  );
}
