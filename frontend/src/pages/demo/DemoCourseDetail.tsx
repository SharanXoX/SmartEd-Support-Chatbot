import { Link, useOutletContext, useParams } from "react-router-dom";
import type { LmsStudentState } from "../../services/mockApi";

export default function DemoCourseDetail() {
  const { courseId } = useParams();
  const { student } = useOutletContext<{ student: LmsStudentState }>();
  const course = student.courses.find((c) => c.id === courseId) ?? student.courses[0];

  if (!course) {
    return (
      <div className="mx-auto max-w-lg text-sm text-slate-600">
        Course not found. <Link to="/demo/courses" className="text-brand-600 hover:underline">Back to courses</Link>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-3xl space-y-4">
      <Link to="/demo/courses" className="text-sm font-medium text-brand-600 hover:underline">
        ← My Courses
      </Link>
      <article className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-slate-900">
        <h2 className="text-2xl font-semibold text-slate-900 dark:text-slate-50">{course.title}</h2>
        <p className="mt-2 text-sm text-slate-600 dark:text-slate-300">
          Next module: <strong>{course.next_module}</strong> · {course.next_due}
        </p>
        <div className="mt-4 h-2 overflow-hidden rounded-full bg-slate-200 dark:bg-slate-800">
          <div className="h-full rounded-full bg-brand-600" style={{ width: `${course.progress_pct}%` }} />
        </div>
        <p className="mt-2 text-xs text-slate-500">{course.progress_pct}% complete</p>
        <button
          type="button"
          className="mt-6 rounded-xl bg-brand-600 px-5 py-2.5 text-sm font-semibold text-white hover:bg-brand-700"
        >
          Continue module
        </button>
      </article>
    </div>
  );
}
