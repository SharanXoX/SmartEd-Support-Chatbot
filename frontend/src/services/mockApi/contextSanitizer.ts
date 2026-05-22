import type { LmsStudentState, MockExam } from "./types";

export function certifiedCourseIds(state: LmsStudentState): Set<string> {
  return new Set(state.certificates.map((c) => c.course_id));
}

export function filterActiveCourses(state: LmsStudentState) {
  const certIds = certifiedCourseIds(state);
  return state.courses.filter(
    (c) => !c.completed && c.progress_pct < 100 && !certIds.has(c.id),
  );
}

export function filterActiveExams(exams: MockExam[]) {
  return exams.filter((e) => e.status === "Scheduled" || e.status === "In review");
}

export function inferQueryFocus(message: string, currentRoute: string): string {
  const route = currentRoute.replace(/\/$/, "") || "/";
  if (route === "/demo/exams") return "exams";
  if (route === "/demo/courses" || route.startsWith("/demo/course/")) return "courses";
  if (route === "/demo/certifications" || route === "/demo/certificates") return "certifications";
  if (route === "/demo/purchases") return "purchases";
  const msg = message.toLowerCase();
  if (/\b(exams?|tests?|assessments?|quizzes?)\b/.test(msg)) return "exams";
  if (/\bwhen\b.*\b(exam|test|quiz)\b/.test(msg)) return "exams";
  if (/\b(certificates?|certifications?)\b/.test(msg)) return "certifications";
  if (/\b(purchases?|orders?|bought)\b/.test(msg)) return "purchases";
  if (/\b(courses?|enrolled)\b/.test(msg)) return "courses";
  return "general";
}
