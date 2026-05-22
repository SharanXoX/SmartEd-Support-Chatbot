import DemoPageShell from "../../components/demo/DemoPageShell";

const DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];
const EVENTS: Record<number, string> = {
  12: "Biology lab",
  18: "Python assignment due",
  22: "UI/UX discussion",
  28: "Biology midterm",
};

export default function DemoCalendar() {
  const cells = Array.from({ length: 35 }, (_, i) => {
    const day = i - 2;
    return day >= 1 && day <= 31 ? day : null;
  });

  return (
    <DemoPageShell title="Calendar" subtitle="Your learning schedule at a glance">
      <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-900">
        <div className="mb-4 flex items-center justify-between">
          <span className="font-semibold text-slate-900 dark:text-slate-50">May 2026</span>
          <span className="text-xs text-slate-500">Demo calendar · no backend sync</span>
        </div>
        <div className="grid grid-cols-7 gap-1 text-center text-xs font-medium text-slate-500">
          {DAYS.map((d) => (
            <div key={d} className="py-2">
              {d}
            </div>
          ))}
        </div>
        <div className="grid grid-cols-7 gap-1">
          {cells.map((day, idx) => (
            <div
              key={idx}
              className={`min-h-[72px] rounded-lg border p-1 text-left text-xs ${
                day
                  ? "border-slate-100 bg-slate-50 dark:border-slate-800 dark:bg-slate-950"
                  : "border-transparent"
              }`}
            >
              {day ? (
                <>
                  <span className="font-medium text-slate-700 dark:text-slate-200">{day}</span>
                  {EVENTS[day] ? (
                    <div className="mt-1 rounded bg-brand-600/10 px-1 py-0.5 text-[10px] text-brand-800 dark:text-brand-200">
                      {EVENTS[day]}
                    </div>
                  ) : null}
                </>
              ) : null}
            </div>
          ))}
        </div>
      </div>
    </DemoPageShell>
  );
}
