import { motion } from "framer-motion";
import { useEffect, useState } from "react";
import type { VisualStep } from "../types";
import { normalizeDemoPath, openPageLabel } from "../lib/navigation";
import ImageCard from "./ImageCard";

function formatInlineBold(text: string) {
  const parts = text.split(/(\*\*[^*]+\*\*)/g);
  return parts.map((part, i) => {
    const m = part.match(/^\*\*(.+)\*\*$/);
    if (m) {
      return (
        <strong key={i} className="font-semibold text-slate-900">
          {m[1]}
        </strong>
      );
    }
    return <span key={i}>{part}</span>;
  });
}

type Props = {
  steps: VisualStep[];
  matchedIntent?: string | null;
  intentConfidence?: number | null;
  onNavigate: (path: string) => void;
  currentRoute: string;
};

export default function SupportFlow({
  steps,
  matchedIntent,
  intentConfidence,
  onNavigate,
  currentRoute,
}: Props) {
  const total = steps.length || 1;
  const [activeIndex, setActiveIndex] = useState(0);
  const flowKey = `${matchedIntent ?? "flow"}-${total}-${steps[0]?.description?.slice(0, 24) ?? ""}`;

  useEffect(() => {
    setActiveIndex(0);
  }, [flowKey]);

  const progress = activeIndex + 1;

  function goToStep(index: number, navigateToStep = false) {
    const clamped = Math.max(0, Math.min(index, total - 1));
    setActiveIndex(clamped);
    if (navigateToStep) {
      const path = normalizeDemoPath(steps[clamped]?.open_url);
      if (path) onNavigate(path);
    }
  }

  function handleOpenPage(index: number) {
    const path = normalizeDemoPath(steps[index]?.open_url);
    if (path) onNavigate(path);
    if (index < total - 1) setActiveIndex(index + 1);
  }

  return (
    <motion.div
      initial="hidden"
      animate="show"
      variants={{
        hidden: {},
        show: { transition: { staggerChildren: 0.06 } },
      }}
      className="mt-3 space-y-4 rounded-xl border border-brand-600/15 bg-gradient-to-b from-brand-600/5 to-transparent p-3 dark:border-brand-400/20 dark:from-brand-400/10"
    >
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className="text-[11px] font-bold uppercase tracking-wide text-violet-900">
          Guided walkthrough
          {matchedIntent ? (
            <span className="ml-2 rounded-full bg-white px-2 py-0.5 font-mono text-[10px] font-semibold normal-case text-slate-800 ring-1 ring-slate-300">
              {matchedIntent}
            </span>
          ) : null}
        </div>
        {intentConfidence != null ? (
          <div className="text-[11px] font-medium text-slate-700">
            Intent match {(intentConfidence * 100).toFixed(0)}%
          </div>
        ) : null}
      </div>

      <div className="text-[11px] font-medium text-slate-700">
        Step {progress} of {total} · tap <strong className="text-slate-900">Open page</strong> to navigate the demo LMS
      </div>

      <div
        className="h-1.5 w-full overflow-hidden rounded-full bg-slate-200 dark:bg-slate-800"
        role="progressbar"
        aria-valuemin={1}
        aria-valuemax={total}
        aria-valuenow={progress}
      >
        <div
          className="h-full rounded-full bg-brand-600/80 transition-all duration-300 dark:bg-brand-400/80"
          style={{ width: `${(progress / total) * 100}%` }}
        />
      </div>

      <div className="space-y-4">
        {steps.map((s, idx) => {
          const isActive = idx === activeIndex;
          const path = normalizeDemoPath(s.open_url);
          const onPage = path === currentRoute;
          const pageLabel = path ? openPageLabel(path) : null;

          return (
            <motion.div
              key={`${s.step}-${idx}`}
              variants={{
                hidden: { opacity: 0, y: 8 },
                show: { opacity: 1, y: 0 },
              }}
              onClick={() => setActiveIndex(idx)}
              className={`cursor-pointer rounded-xl border p-3 shadow-sm transition ${
                isActive
                  ? "border-brand-500 bg-white ring-2 ring-brand-500/30 dark:border-brand-400 dark:bg-slate-950/90"
                  : "border-slate-200 bg-white/70 opacity-80 dark:border-slate-800 dark:bg-slate-950/50"
              }`}
            >
              <div className="text-xs font-semibold text-slate-700">
                Step {(s.step ?? idx + 1).toString()} <span className="text-slate-500">/</span> {total}
                {isActive ? (
                  <span className="ml-2 font-bold text-violet-800">· current</span>
                ) : null}
              </div>
              <div className="mt-1 text-sm font-semibold text-slate-900">{s.title}</div>
              <div className="mt-1 text-sm font-medium leading-relaxed text-slate-800">
                {formatInlineBold(s.description)}
              </div>

              {path ? (
                <div className="mt-3 flex flex-wrap gap-2">
                  <button
                    type="button"
                    onClick={(e) => {
                      e.stopPropagation();
                      handleOpenPage(idx);
                    }}
                    className="rounded-lg bg-violet-700 px-3 py-1.5 text-xs font-semibold text-white hover:bg-violet-800"
                  >
                    {onPage ? `On ${pageLabel}` : `Open ${pageLabel}`}
                  </button>
                  {idx < total - 1 ? (
                    <button
                      type="button"
                      onClick={(e) => {
                        e.stopPropagation();
                        goToStep(idx + 1, false);
                      }}
                      className="rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-xs font-semibold text-slate-800 hover:bg-slate-50"
                    >
                      Continue
                    </button>
                  ) : null}
                  {idx < total - 1 ? (
                    <button
                      type="button"
                      onClick={(e) => {
                        e.stopPropagation();
                        goToStep(idx + 1, true);
                      }}
                      className="rounded-lg border border-violet-300 bg-violet-50 px-3 py-1.5 text-xs font-semibold text-violet-900 hover:bg-violet-100"
                    >
                      Next step →
                    </button>
                  ) : null}
                </div>
              ) : null}

              {s.image_url ? (
                <ImageCard
                  src={s.image_url}
                  alt={s.title}
                  caption={undefined}
                  stepLabel={`Screenshot · ${s.step ?? idx + 1}/${total}`}
                />
              ) : (
                <div className="mt-3 rounded-lg border border-dashed border-slate-300 bg-slate-50 px-3 py-6 text-center text-xs text-slate-500 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-400">
                  Screenshot missing for this step
                </div>
              )}
            </motion.div>
          );
        })}
      </div>
    </motion.div>
  );
}
