import { useOutletContext } from "react-router-dom";
import DemoPageShell from "../../components/demo/DemoPageShell";
import type { LmsStudentState } from "../../services/mockApi";

export default function DemoAnnouncements() {
  const { student } = useOutletContext<{ student: LmsStudentState }>();
  const items = student.announcements;

  return (
    <DemoPageShell title="Announcements" subtitle="Updates from your instructors and the platform">
      {items.length === 0 ? (
        <div className="rounded-2xl border border-slate-200 bg-white p-10 text-center shadow-sm dark:border-slate-800 dark:bg-slate-900">
          <p className="text-sm text-slate-600 dark:text-slate-300">No announcements available.</p>
        </div>
      ) : (
        <div className="space-y-3">
          {items.map((a) => (
            <article
              key={a.id}
              className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-900"
            >
              <div className="flex flex-wrap items-baseline justify-between gap-2">
                <h3 className="font-semibold text-slate-900 dark:text-slate-50">{a.title}</h3>
                <span className="text-xs text-slate-500">{a.date}</span>
              </div>
              <p className="mt-2 text-sm text-slate-600 dark:text-slate-300">{a.content}</p>
            </article>
          ))}
        </div>
      )}
    </DemoPageShell>
  );
}
