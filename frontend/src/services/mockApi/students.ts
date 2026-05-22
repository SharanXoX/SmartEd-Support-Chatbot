import { api } from "../../api/client";
import { FALLBACK_ALEX } from "./fallbackData";
import type { LmsStudentState, StudentProfileOption } from "./types";

const STORAGE_KEY = "smarted_active_user_id";

const LEGACY_ID_MAP: Record<string, string> = {
  "demo-001": "alex-001",
  "demo-002": "priya-001",
  "demo-003": "sam-001",
  "demo-004": "priya-001",
};

export function getActiveStudentId(): string {
  const raw = localStorage.getItem(STORAGE_KEY) || localStorage.getItem("smarted_mock_student_id");
  const id = raw || FALLBACK_ALEX.student_id;
  return LEGACY_ID_MAP[id] ?? id;
}

export function setActiveStudentId(studentId: string): void {
  const mapped = LEGACY_ID_MAP[studentId] ?? studentId;
  localStorage.setItem(STORAGE_KEY, mapped);
  localStorage.setItem("smarted_mock_student_id", mapped);
}

function normalizeState(raw: Record<string, unknown>): LmsStudentState {
  const progressRaw = raw.progress as Record<string, number> | undefined;
  const courses = (raw.courses as LmsStudentState["courses"]) ?? [];
  const progress: Record<string, number> = progressRaw ?? {};
  if (!Object.keys(progress).length) {
    for (const c of courses) {
      progress[c.id] = c.progress_pct;
    }
  }
  return {
    student_id: String(raw.student_id ?? raw.id ?? ""),
    name: String(raw.name ?? "Student"),
    email: String(raw.email ?? ""),
    role: String(raw.role ?? "learner"),
    profile_type: raw.profile_type ? String(raw.profile_type) : undefined,
    courses,
    exams: (raw.exams as LmsStudentState["exams"]) ?? [],
    purchases: (raw.purchases as LmsStudentState["purchases"]) ?? [],
    certificates: (raw.certificates as LmsStudentState["certificates"]) ?? [],
    announcements: (raw.announcements as LmsStudentState["announcements"]) ?? [],
    recent_activity:
      (raw.recent_activity as LmsStudentState["recent_activity"]) ??
      (raw.recentActivity as LmsStudentState["recent_activity"]) ??
      [],
    progress,
  };
}

export async function fetchStudentState(studentId?: string): Promise<LmsStudentState> {
  const id = studentId ?? getActiveStudentId();
  try {
    const resp = await api.get<Record<string, unknown>>("/demo/student", {
      params: { student_id: id },
      timeout: 5000,
    });
    return normalizeState(resp.data);
  } catch {
    if (id === FALLBACK_ALEX.student_id) return FALLBACK_ALEX;
    return fetchStudentState(FALLBACK_ALEX.student_id);
  }
}

export async function listStudents(): Promise<StudentProfileOption[]> {
  try {
    const resp = await api.get<{ students: StudentProfileOption[] }>("/demo/students");
    return resp.data.students ?? [];
  } catch {
    return [
      { id: "alex-001", name: "Alex", profile_type: "beginner" },
      { id: "sam-001", name: "Sam", profile_type: "overdue" },
      { id: "priya-001", name: "Priya", profile_type: "advanced" },
      { id: "john-001", name: "John", profile_type: "new" },
    ];
  }
}

export function upcomingExams(state: LmsStudentState) {
  return state.exams.filter(
    (e) => e.status === "Scheduled" || e.status === "In review",
  );
}

export function completedCourses(
  state: LmsStudentState | { courses: { progress_pct: number; completed?: boolean }[] },
) {
  return state.courses.filter((c) => c.progress_pct >= 100 || c.completed);
}
