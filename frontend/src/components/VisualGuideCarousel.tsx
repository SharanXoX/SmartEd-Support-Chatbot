import { motion } from "framer-motion";
import { useId, useMemo, useState } from "react";
import type { VisualStep } from "../types";
import { resolveAssetUrl } from "../api/client";

type Props = {
  steps: VisualStep[];
};

export default function VisualGuideCarousel({ steps }: Props) {
  const markerId = useId().replace(/:/g, "");
  const items = useMemo(() => steps.filter((s) => s.title || s.description || s.image_url), [steps]);
  const [idx, setIdx] = useState(0);

  if (!items.length) return null;

  const step = items[idx];

  return (
    <div className="mt-3 rounded-xl border border-slate-200 bg-white p-3 shadow-sm dark:border-slate-700 dark:bg-slate-900">
      <div className="mb-2 flex items-center justify-between gap-2">
        <div className="text-xs font-semibold uppercase tracking-wide text-slate-700">
          Visual guidance · Step {step.step ?? idx + 1}
        </div>
        <div className="flex gap-1">
          <button
            type="button"
            className="rounded-md border border-slate-300 bg-white px-2 py-1 text-xs font-medium text-slate-800 hover:bg-slate-50"
            onClick={() => setIdx((v) => Math.max(0, v - 1))}
            disabled={idx === 0}
          >
            Prev
          </button>
          <button
            type="button"
            className="rounded-md border border-slate-300 bg-white px-2 py-1 text-xs font-medium text-slate-800 hover:bg-slate-50"
            onClick={() => setIdx((v) => Math.min(items.length - 1, v + 1))}
            disabled={idx >= items.length - 1}
          >
            Next
          </button>
        </div>
      </div>

      <div className="text-sm font-semibold text-slate-900">{step.title}</div>
      <div className="mt-1 text-sm font-medium leading-relaxed text-slate-800">{step.description}</div>

      {step.image_url ? (
        <motion.div layout className="relative mt-3 overflow-hidden rounded-lg bg-slate-100 dark:bg-slate-800">
          <img
            src={resolveAssetUrl(step.image_url)}
            alt={step.title}
            className="max-h-72 w-full object-contain"
          />

          <svg viewBox="0 0 100 100" preserveAspectRatio="none" className="pointer-events-none absolute inset-0 h-full w-full">
            <defs>
              <marker id={markerId} markerWidth="6" markerHeight="6" refX="5" refY="3" orient="auto">
                <polygon points="0 0, 6 3, 0 6" fill="#ef4444" />
              </marker>
            </defs>
            {step.annotations?.map((a, i) => {
              const kind = a.kind ?? "highlight";
              const x = (a.x ?? 0) * 100;
              const y = (a.y ?? 0) * 100;
              const w = (a.w ?? 0.2) * 100;
              const h = (a.h ?? 0.1) * 100;

              if (kind === "circle") {
                const cx = x + w / 2;
                const cy = y + h / 2;
                const r = Math.max(w, h) / 2;
                return (
                  <ellipse
                    key={i}
                    cx={`${cx}%`}
                    cy={`${cy}%`}
                    rx={`${r}%`}
                    ry={`${r}%`}
                    fill="none"
                    stroke="#f97316"
                    strokeWidth="1.2"
                  />
                );
              }

              if (kind === "arrow") {
                const x2 = x + w;
                const y2 = y + h;
                return (
                  <line
                    key={i}
                    x1={`${x}%`}
                    y1={`${y}%`}
                    x2={`${x2}%`}
                    y2={`${y2}%`}
                    stroke="#ef4444"
                    strokeWidth="1.5"
                    markerEnd={`url(#${markerId})`}
                  />
                );
              }

              return (
                <rect
                  key={i}
                  x={`${x}%`}
                  y={`${y}%`}
                  width={`${w}%`}
                  height={`${h}%`}
                  fill="rgba(250, 204, 21, 0.25)"
                  stroke="rgba(234, 179, 8, 0.85)"
                  strokeWidth="1"
                />
              );
            })}
          </svg>
        </motion.div>
      ) : null}

      <div className="mt-2 flex gap-1">
        {items.map((_, i) => (
          <button
            key={i}
            type="button"
            className={`h-1.5 flex-1 rounded-full ${i === idx ? "bg-brand-600" : "bg-slate-200 dark:bg-slate-700"}`}
            onClick={() => setIdx(i)}
            aria-label={`Go to step ${i + 1}`}
          />
        ))}
      </div>
    </div>
  );
}
