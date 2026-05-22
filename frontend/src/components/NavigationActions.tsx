import type { NavigationAction } from "../types";
import { openPageLabel } from "../lib/navigation";

type Props = {
  actions: NavigationAction[];
  onNavigate: (path: string) => void;
  currentRoute: string;
};

export default function NavigationActions({ actions, onNavigate, currentRoute }: Props) {
  if (!actions.length) return null;

  return (
    <div className="mt-2 flex flex-wrap gap-2">
      {actions.map((a) => {
        const path = a.path.startsWith("/") ? a.path : `/${a.path}`;
        const isHere = path === currentRoute;
        return (
          <button
            key={`${a.label}-${path}`}
            type="button"
            disabled={isHere}
            onClick={() => onNavigate(path)}
            className="rounded-lg bg-violet-700 px-3 py-1.5 text-xs font-semibold text-white shadow-sm hover:bg-violet-800 disabled:cursor-default disabled:opacity-60"
          >
            {isHere ? `On ${a.label}` : a.label}
          </button>
        );
      })}
    </div>
  );
}

export function navigationLabelFromPath(path: string): string {
  return `Open ${openPageLabel(path)}`;
}
