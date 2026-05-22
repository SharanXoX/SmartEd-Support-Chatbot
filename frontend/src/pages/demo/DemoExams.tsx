import { useOutletContext } from "react-router-dom";
import DemoPageShell from "../../components/demo/DemoPageShell";
import type { LmsStudentState } from "../../services/mockApi";

export default function DemoExams() {
  const { student } = useOutletContext<{ student: LmsStudentState }>();

  return (
    <DemoPageShell title="Exams" subtitle="Upcoming assessments across your enrolled courses">
      <div className="space-y-3">
        {student.exams.map((exam) => (
          <article
            key={exam.id}
            className="flex flex-wrap items-center justify-between gap-4 rounded-2xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-900"
          >
            <div>
              <h3 className="font-semibold text-slate-900 dark:text-slate-50">{exam.title}</h3>
              <p className="text-sm text-slate-600 dark:text-slate-300">{exam.course}</p>
              <p className="mt-1 text-xs text-slate-500">{exam.date}</p>
              {exam.score != null ? (
                <p className="mt-1 text-xs font-medium text-brand-600">Score: {exam.score}%</p>
              ) : null}
            </div>
            <span
              className={`rounded-full px-3 py-1 text-xs font-semibold ring-1 ${
                exam.status === "Completed"
                  ? "bg-emerald-500/10 text-emerald-800 ring-emerald-500/20 dark:text-emerald-200"
                  : "bg-amber-500/10 text-amber-800 ring-amber-500/20 dark:text-amber-200"
              }`}
            >
              {exam.status}
            </span>
          </article>
        ))}
      </div>
    </DemoPageShell>
  );
}
