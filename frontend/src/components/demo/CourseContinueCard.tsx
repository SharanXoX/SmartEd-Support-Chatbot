import { Link } from "react-router-dom";
import type { MockCourse } from "../../services/mockApi";

const CARD_GRADIENTS = [
  "from-violet-500/20 to-indigo-600/30",
  "from-sky-500/20 to-blue-600/30",
  "from-emerald-500/20 to-teal-600/30",
  "from-amber-500/20 to-orange-600/30",
];

type CourseContinueCardProps = {
  course: MockCourse;
  index?: number;
};

export default function CourseContinueCard({ course, index = 0 }: CourseContinueCardProps) {
  const gradient = CARD_GRADIENTS[index % CARD_GRADIENTS.length];
  const subtitle = course.instructor
    ? `Instructor: ${course.instructor}`
    : course.next_module || "Continue your learning path";

  return (
    <article className="flex gap-4 rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
      <div
        className={`flex h-20 w-28 shrink-0 items-center justify-center rounded-md bg-gradient-to-br ${gradient} text-2xl text-violet-700/80`}
        aria-hidden
      >
        📚
      </div>
      <div className="min-w-0 flex-1">
        <h3 className="text-sm font-bold uppercase tracking-wide text-slate-800">{course.title}</h3>
        <p className="mt-0.5 line-clamp-2 text-xs text-slate-500">{subtitle}</p>
        <div className="mt-3 h-1.5 overflow-hidden rounded-full bg-slate-200">
          <div
            className="h-full rounded-full bg-violet-600 transition-all"
            style={{ width: `${Math.min(100, Math.max(0, course.progress_pct))}%` }}
          />
        </div>
        <p className="mt-1 text-right text-xs font-medium text-violet-700">{course.progress_pct}%</p>
        <Link
          to={`/demo/course/${course.id}`}
          className="mt-2 inline-block text-xs font-semibold text-violet-700 hover:text-violet-900"
        >
          Continue →
        </Link>
      </div>
    </article>
  );
}
