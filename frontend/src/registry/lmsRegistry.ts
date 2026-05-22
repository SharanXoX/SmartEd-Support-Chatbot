/** Canonical LMS features and routes — must match backend lms_feature_registry.py */

export const AVAILABLE_LMS_FEATURES = [
  "dashboard",
  "announcements",
  "courses",
  "calendar",
  "exams",
  "certifications",
  "purchases",
  "profile",
  "settings",
  "help",
] as const;

export type LmsFeatureId = (typeof AVAILABLE_LMS_FEATURES)[number];

export const AVAILABLE_LMS_ROUTES: Record<LmsFeatureId, string> = {
  dashboard: "/demo/dashboard",
  announcements: "/demo/announcements",
  courses: "/demo/courses",
  calendar: "/demo/calendar",
  exams: "/demo/exams",
  certifications: "/demo/certifications",
  purchases: "/demo/purchases",
  profile: "/demo/profile",
  settings: "/demo/settings",
  help: "/demo/help",
};

export const NAV_ITEMS = [
  { label: "Dashboard", path: AVAILABLE_LMS_ROUTES.dashboard, icon: "⌂", feature: "dashboard" as const },
  { label: "Announcements", path: AVAILABLE_LMS_ROUTES.announcements, icon: "📢", feature: "announcements" as const },
  { label: "My Courses", path: AVAILABLE_LMS_ROUTES.courses, icon: "▤", feature: "courses" as const },
  { label: "Calendar", path: AVAILABLE_LMS_ROUTES.calendar, icon: "📅", feature: "calendar" as const },
  { label: "Exams", path: AVAILABLE_LMS_ROUTES.exams, icon: "📝", feature: "exams" as const },
  { label: "Certifications", path: AVAILABLE_LMS_ROUTES.certifications, icon: "🏅", feature: "certifications" as const },
  { label: "My Purchases", path: AVAILABLE_LMS_ROUTES.purchases, icon: "🛒", feature: "purchases" as const },
  { label: "Profile", path: AVAILABLE_LMS_ROUTES.profile, icon: "👤", feature: "profile" as const },
  { label: "Settings", path: AVAILABLE_LMS_ROUTES.settings, icon: "⚙", feature: "settings" as const },
  { label: "Help", path: AVAILABLE_LMS_ROUTES.help, icon: "❓", feature: "help" as const },
] as const;

export const QUICK_ACTIONS = [
  { label: "My Courses", message: "Where are my courses?", navigateTo: AVAILABLE_LMS_ROUTES.courses },
  { label: "Exams", message: "What are my upcoming exams?", navigateTo: AVAILABLE_LMS_ROUTES.exams },
  { label: "Submit Assignment", message: "How do I submit an assignment?" },
  { label: "Certifications", message: "Show my certificates", navigateTo: AVAILABLE_LMS_ROUTES.certifications },
  { label: "Profile", message: "Edit my profile", navigateTo: AVAILABLE_LMS_ROUTES.profile },
  { label: "Settings", message: "Open settings", navigateTo: AVAILABLE_LMS_ROUTES.settings },
  { label: "Contact Support", message: "I need human help" },
] as const;

export const TICKET_TRIGGER =
  /\b(contact support|human help|talk to admin|need human|speak to support|create ticket)\b/i;

export function routeToPageLabel(path: string): string {
  const item = NAV_ITEMS.find((n) => n.path === path);
  return item?.label ?? path;
}
