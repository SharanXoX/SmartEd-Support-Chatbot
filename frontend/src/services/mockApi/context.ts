import {
  AVAILABLE_LMS_FEATURES,
  AVAILABLE_LMS_ROUTES,
  routeToPageLabel,
} from "../../registry/lmsRegistry";
import { filterActiveCourses, filterActiveExams } from "./contextSanitizer";
import type { ActiveUserSnapshot, LmsContextSnapshot, LmsStudentState } from "./types";

export function toActiveUserSnapshot(state: LmsStudentState): ActiveUserSnapshot {
  const progress: Record<string, number> = {};
  if (state.progress) {
    Object.assign(progress, state.progress);
  } else {
    for (const c of state.courses) {
      progress[c.id] = c.progress_pct;
    }
  }
  const activeCourses = filterActiveCourses(state);
  const activeExams = filterActiveExams(state.exams);
  return {
    id: state.student_id,
    name: state.name,
    email: state.email,
    role: state.role,
    profile_type: state.profile_type,
    purchases: state.purchases,
    courses: activeCourses,
    certificates: state.certificates,
    upcomingExams: activeExams,
    progress,
  };
}

export function buildLmsContextSnapshot(
  state: LmsStudentState,
  currentRoute: string,
): LmsContextSnapshot {
  const activeUser = toActiveUserSnapshot(state);
  return {
    current_route: currentRoute,
    current_page: routeToPageLabel(currentRoute),
    student_id: state.student_id,
    activeUser,
    student: {
      student_id: state.student_id,
      name: state.name,
      email: state.email,
      role: state.role,
    },
    courses: activeUser.courses,
    purchases: state.purchases,
    upcoming_exams: activeUser.upcomingExams,
    recent_activity: state.recent_activity,
    available_features: [...AVAILABLE_LMS_FEATURES],
    available_routes: { ...AVAILABLE_LMS_ROUTES },
    certificates_count: state.certificates.length,
    has_enrolled_courses: state.courses.length > 0,
    has_purchases: state.purchases.length > 0,
  };
}
