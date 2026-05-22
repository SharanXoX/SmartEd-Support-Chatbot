import { Link, useOutletContext } from "react-router-dom";
import type { LmsStudentState } from "../../services/mockApi";

export default function DemoCourses() {
  const { student } = useOutletContext<{ student: LmsStudentState }>();

  return (
    <div className="mx-auto max-w-4xl space-y-4">
      <h2 className="text-xl font-semibold text-slate-900 dark:text-slate-50">My Courses</h2>
      <div className="grid gap-4">
        {student.courses.length === 0 ? (
          <div className="rounded-2xl border border-dashed border-slate-300 bg-white p-10 text-center dark:border-slate-700 dark:bg-slate-900">
            <p className="text-sm text-slate-600 dark:text-slate-300">
              You have not enrolled in any courses yet. Browse the catalog or ask the assistant how to get started.
            </p>
          </div>
        ) : null}
        {student.courses.map((c) => (
          <article
            key={c.id}
            className="flex flex-wrap items-center justify-between gap-4 rounded-2xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-900"
          >
            <div>
              <h3 className="font-semibold text-slate-900 dark:text-slate-50">{c.title}</h3>
              {c.instructor ? (
                <p className="text-xs text-slate-500">Instructor: {c.instructor}</p>
              ) : null}
              <p className="text-sm text-slate-500">Next module: {c.next_module}</p>
              <p className="text-xs text-slate-400">{c.next_due}</p>
            </div>
            <div className="flex items-center gap-3">
              <div className="text-right">
                <div className="text-2xl font-bold text-brand-600">{c.progress_pct}%</div>
                <div className="text-xs text-slate-500">progress</div>
              </div>
              <Link
                to={`/demo/course/${c.id}`}
                className="rounded-xl bg-brand-600 px-4 py-2 text-sm font-semibold text-white hover:bg-brand-700"
              >
                Continue
              </Link>
            </div>
          </article>
        ))}
      </div>
    </div>
  );
}
