import { useEffect } from "react";
import { Link, NavLink, Outlet } from "react-router-dom";
import FloatingChat from "../components/FloatingChat";
import { useLmsState } from "../context/LmsStateContext";
import { NAV_ITEMS } from "../registry/lmsRegistry";

/** Mock LMS chrome aligned with elearn.smarted.pro (light, purple, sidebar + top bar). */
export default function LmsDemoLayout() {
  const { state } = useLmsState();

  useEffect(() => {
    document.documentElement.classList.remove("dark");
    localStorage.setItem("theme", "light");
  }, []);

  return (
    <div className="flex min-h-screen flex-col bg-[#f4f5f8]">
      {/* Top bar — matches production LMS header */}
      <header className="z-40 flex shrink-0 items-center gap-4 border-b border-slate-200 bg-white px-4 py-3 md:px-6">
        <Link to="/demo/dashboard" className="shrink-0 text-2xl font-bold tracking-tight text-violet-700">
          smarted
        </Link>
        <div className="mx-auto hidden max-w-2xl flex-1 md:block">
          <input
            type="search"
            placeholder="Search for Courses, Subjects, Sections or Lessons"
            className="w-full rounded-md border border-slate-200 bg-slate-50 px-4 py-2.5 text-sm text-slate-700 outline-none ring-violet-600 focus:ring-2"
          />
        </div>
        <div className="ml-auto flex items-center gap-3">
          <Link
            to="/demo/courses"
            className="hidden text-sm font-medium text-violet-700 hover:text-violet-900 sm:inline"
          >
            Explore Courses
          </Link>
          <button
            type="button"
            className="rounded-full p-2 text-slate-500 hover:bg-violet-50"
            aria-label="Messages"
          >
            💬
          </button>
          <div className="flex items-center gap-2 rounded-full border border-slate-200 bg-white py-1 pl-1 pr-3">
            <div className="flex h-8 w-8 items-center justify-center rounded-full bg-sky-500 text-xs font-bold text-white">
              {state.name.charAt(0)}
            </div>
            <span className="text-sm font-medium text-slate-700">{state.name}</span>
            <span className="text-xs text-slate-400">▾</span>
          </div>
        </div>
      </header>

      <div className="flex min-h-0 flex-1">
        {/* Left sidebar — production order & labels */}
        <aside className="hidden w-52 shrink-0 flex-col border-r border-slate-200 bg-white md:flex lg:w-56">
          <nav className="flex-1 space-y-0.5 p-2 pt-4">
            {NAV_ITEMS.map((item) => (
              <NavLink
                key={item.path}
                to={item.path}
                className={({ isActive }) =>
                  `flex items-center gap-3 rounded-md px-3 py-2.5 text-sm font-medium transition ${
                    isActive
                      ? "bg-violet-100 text-violet-800"
                      : "text-slate-600 hover:bg-slate-50 hover:text-violet-700"
                  }`
                }
              >
                <span className="text-base opacity-80">{item.icon}</span>
                {item.label === "Certifications" ? "Certificates" : item.label}
              </NavLink>
            ))}
          </nav>
        </aside>

        <main className="min-w-0 flex-1 overflow-y-auto p-4 md:p-6">
          <Outlet context={{ student: state }} />
        </main>
      </div>

      <FloatingChat studentName={state.name} studentEmail={state.email} />
    </div>
  );
}
