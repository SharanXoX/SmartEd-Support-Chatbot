import { useOutletContext } from "react-router-dom";
import DemoPageShell from "../../components/demo/DemoPageShell";
import { completedCourses, type LmsStudentState } from "../../services/mockApi";

export default function DemoCertifications() {
  const { student } = useOutletContext<{ student: LmsStudentState }>();
  const certs = student.certificates;
  const completed = completedCourses(student);

  return (
    <DemoPageShell
      title="Certifications"
      subtitle="Certificates are issued when you complete a course (100% progress)"
    >
      {certs.length === 0 ? (
        <div className="rounded-2xl border border-dashed border-slate-300 bg-white p-10 text-center dark:border-slate-700 dark:bg-slate-900">
          <p className="text-sm text-slate-600 dark:text-slate-300">
            Certificates will appear after course completion.
          </p>
          <p className="mt-2 text-xs text-slate-500">
            {completed.length > 0
              ? "Your completed courses are being processed."
              : "Finish all modules in a course to unlock your certificate here."}
          </p>
        </div>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2">
          {certs.map((c) => (
            <article
              key={c.id}
              className="rounded-2xl border border-emerald-200 bg-emerald-50/50 p-5 dark:border-emerald-900 dark:bg-emerald-950/30"
            >
              <div className="text-xs font-semibold uppercase text-emerald-700 dark:text-emerald-300">
                Certificate earned
              </div>
              <h3 className="mt-2 font-semibold text-slate-900 dark:text-slate-50">{c.course_title}</h3>
              <p className="mt-1 text-xs text-slate-500">Issued {c.issued_at}</p>
              <button
                type="button"
                className="mt-4 rounded-xl bg-brand-600 px-4 py-2 text-sm font-semibold text-white hover:bg-brand-700"
              >
                Download PDF
              </button>
            </article>
          ))}
        </div>
      )}
    </DemoPageShell>
  );
}
