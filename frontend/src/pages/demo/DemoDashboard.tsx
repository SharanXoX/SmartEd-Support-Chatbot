import type { ReactNode } from "react";
import { Link, useOutletContext } from "react-router-dom";
import CourseContinueCard from "../../components/demo/CourseContinueCard";
import { filterActiveCourses } from "../../services/mockApi/contextSanitizer";
import type { LmsStudentState } from "../../services/mockApi";

function PanelHeader({ title, actions }: { title: string; actions?: ReactNode }) {
  return (
    <div className="flex items-center justify-between rounded-t-lg bg-violet-700 px-4 py-2.5 text-white">
      <h2 className="text-sm font-semibold">{title}</h2>
      {actions ? <div className="flex items-center gap-2 text-sm opacity-90">{actions}</div> : null}
    </div>
  );
}

export default function DemoDashboard() {
  const { student } = useOutletContext<{ student: LmsStudentState }>();
  const activeCourses = filterActiveCourses(student);
  const displayCourses = activeCourses.length > 0 ? activeCourses : student.courses;
  const empty = student.courses.length === 0;

  return (
    <div className="mx-auto max-w-6xl">
      <div className="grid gap-6 lg:grid-cols-3">
        {/* Left — Continue Learning (production layout) */}
        <section className="lg:col-span-2">
          <h2 className="mb-4 text-base font-bold text-violet-700">Continue Learning</h2>
          {empty ? (
            <div className="rounded-lg border border-dashed border-slate-300 bg-white p-8 text-center">
              <p className="text-sm text-slate-600">
                You have not enrolled in any courses yet. Browse the catalog to get started.
              </p>
              <Link
                to="/demo/courses"
                className="mt-4 inline-block text-sm font-bold uppercase tracking-wide text-violet-700 hover:underline"
              >
                See My Courses
              </Link>
            </div>
          ) : (
            <div className="space-y-4">
              {displayCourses.slice(0, 4).map((c, i) => (
                <CourseContinueCard key={c.id} course={c} index={i} />
              ))}
              <Link
                to="/demo/courses"
                className="inline-block pt-2 text-sm font-bold uppercase tracking-wide text-violet-700 hover:text-violet-900"
              >
                See My Courses
              </Link>
            </div>
          )}
        </section>

        {/* Right — Today's Classes + Class Updates */}
        <div className="space-y-6">
          <section className="overflow-hidden rounded-lg border border-slate-200 bg-white shadow-sm">
            <PanelHeader
              title="Today's Classes"
              actions={
                <>
                  <button type="button" className="hover:opacity-80" aria-label="Refresh">
                    ↻
                  </button>
                  <button type="button" className="hover:opacity-80" aria-label="Calendar">
                    📅
                  </button>
                </>
              }
            />
            <div className="px-4 py-10 text-center text-sm text-slate-500">No Classes</div>
          </section>

          <section className="overflow-hidden rounded-lg border border-slate-200 bg-white shadow-sm">
            <PanelHeader title="Class Updates" />
            <div className="px-4 py-10 text-center text-sm text-slate-500">No Updates</div>
          </section>
        </div>
      </div>
    </div>
  );
}
