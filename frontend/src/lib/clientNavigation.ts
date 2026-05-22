import { AVAILABLE_LMS_ROUTES } from "../registry/lmsRegistry";
import { normalizeDemoPath } from "./navigation";

/** Lightweight client mirror of backend route keywords for navigate-only fallback. */
const ROUTE_HINTS: { path: string; keywords: string[] }[] = [
  { path: AVAILABLE_LMS_ROUTES.dashboard, keywords: ["dashboard", "home"] },
  { path: AVAILABLE_LMS_ROUTES.announcements, keywords: ["announcements", "announcement"] },
  {
    path: AVAILABLE_LMS_ROUTES.courses,
    keywords: ["my courses", "courses", "course list", "get a course", "find a course"],
  },
  { path: AVAILABLE_LMS_ROUTES.calendar, keywords: ["calendar", "schedule"] },
  { path: AVAILABLE_LMS_ROUTES.exams, keywords: ["exams", "my exams", "upcoming exams"] },
  {
    path: AVAILABLE_LMS_ROUTES.certifications,
    keywords: ["certifications", "certificates", "my certificates"],
  },
  { path: AVAILABLE_LMS_ROUTES.purchases, keywords: ["purchases", "my purchases"] },
  {
    path: AVAILABLE_LMS_ROUTES.profile,
    keywords: ["my profile", "check my profile", "view my profile", "profile"],
  },
  { path: AVAILABLE_LMS_ROUTES.settings, keywords: ["settings", "open settings"] },
  { path: AVAILABLE_LMS_ROUTES.help, keywords: ["help", "support"] },
];

const NAV_PHRASE =
  /\b(open|go\s+to|check|show|view|see|find|take\s+me|navigate|where\s+(?:is|are))\b/i;
const COURSE_LOOKUP = /\b(get|find|browse)\s+(?:a\s+)?course/i;

export function matchClientNavigation(message: string): string | null {
  const msg = message.toLowerCase().trim();
  if (!msg) return null;
  if (!NAV_PHRASE.test(msg) && !COURSE_LOOKUP.test(msg)) return null;

  let best: { path: string; score: number } | null = null;
  for (const route of ROUTE_HINTS) {
    for (const kw of route.keywords) {
      if (msg.includes(kw)) {
        const score = kw.length;
        if (!best || score > best.score) {
          best = { path: route.path, score };
        }
      }
    }
  }
  return best ? normalizeDemoPath(best.path) : null;
}
