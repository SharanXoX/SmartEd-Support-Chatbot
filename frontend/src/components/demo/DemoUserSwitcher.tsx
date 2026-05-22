import clsx from "clsx";
import { useLmsState } from "../../context/LmsStateContext";

type DemoUserSwitcherProps = {
  compact?: boolean;
};

const selectClass = (compact?: boolean) =>
  clsx(
    "w-full max-w-md rounded-md border border-slate-300 bg-white px-3 py-2.5 text-sm font-medium text-slate-800 shadow-sm",
    "transition-colors appearance-none cursor-pointer",
    "hover:border-violet-400 hover:bg-violet-50",
    "focus:border-violet-600 focus:outline-none focus:ring-2 focus:ring-violet-200",
    "disabled:cursor-not-allowed disabled:opacity-60",
    "dark:border-slate-500 dark:bg-white dark:text-slate-800 dark:hover:bg-violet-50",
    compact ? "w-full max-w-none" : "mt-2",
  );

export default function DemoUserSwitcher({ compact }: DemoUserSwitcherProps) {
  const { studentProfiles, activeStudentId, setActiveStudent, loading } = useLmsState();

  return (
    <div className={compact ? "" : "mt-3"}>
      {!compact ? (
        <>
          <h3 className="text-sm font-semibold text-slate-900">Switch Demo User</h3>
          <p className="mt-1 text-xs text-slate-600">
            Change the active learner to test personalized AI and LMS state (browser session only).
          </p>
        </>
      ) : null}
      <label className={compact ? "sr-only" : "mt-3 block text-xs font-medium text-slate-600"}>
        Switch Demo User
      </label>
      <select
        className={clsx("demo-user-switcher", selectClass(compact))}
        value={activeStudentId}
        disabled={loading}
        onChange={(e) => void setActiveStudent(e.target.value)}
      >
        {studentProfiles.map((p) => (
          <option
            key={p.id}
            value={p.id}
            className="bg-white py-2 font-medium text-slate-800 dark:bg-white dark:text-slate-800"
          >
            {p.name} ({p.profile_type})
          </option>
        ))}
      </select>
    </div>
  );
}
