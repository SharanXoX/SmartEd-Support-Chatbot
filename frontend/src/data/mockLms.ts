/**
 * Backward-compatible re-exports. Prefer registry/lmsRegistry and services/mockApi.
 */
export {
  AVAILABLE_LMS_FEATURES,
  AVAILABLE_LMS_ROUTES,
  NAV_ITEMS,
  QUICK_ACTIONS,
  TICKET_TRIGGER,
} from "../registry/lmsRegistry";

export type {
  MockCourse,
  MockExam,
  MockPurchase,
  LmsStudentState,
} from "../services/mockApi/types";

export {
  completedCourses,
  upcomingExams,
  FALLBACK_ALEX,
  FALLBACK_ALEX as DEFAULT_STUDENT,
} from "../services/mockApi";

import type { LmsStudentState } from "../services/mockApi/types";

/** @deprecated Use LmsStudentState */
export type MockStudent = Pick<
  LmsStudentState,
  "student_id" | "name" | "role" | "email" | "courses"
>;
