import { useOutletContext } from "react-router-dom";
import DemoPageShell from "../../components/demo/DemoPageShell";
import type { LmsStudentState } from "../../services/mockApi";

export default function DemoPurchases() {
  const { student } = useOutletContext<{ student: LmsStudentState }>();

  return (
    <DemoPageShell title="My Purchases" subtitle="Courses you have purchased on the platform">
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {student.purchases.map((p) => (
          <article
            key={p.id}
            className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-900"
          >
            <h3 className="font-semibold text-slate-900 dark:text-slate-50">{p.courseTitle}</h3>
            <p className="mt-2 text-xs text-slate-500">Purchased {p.purchasedAt}</p>
            <p className="mt-4 text-lg font-bold text-brand-600">{p.price}</p>
          </article>
        ))}
      </div>
    </DemoPageShell>
  );
}
