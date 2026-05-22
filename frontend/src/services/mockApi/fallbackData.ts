import type { LmsStudentState } from "./types";

/** Offline fallback — Alex (beginner, 2 courses). */
export const FALLBACK_ALEX: LmsStudentState = {
  student_id: "alex-001",
  name: "Alex",
  email: "alex.demo@smarted.test",
  role: "learner",
  profile_type: "beginner",
  courses: [
    {
      id: "BIO101",
      title: "Introduction to Biology",
      instructor: "Dr. Chen",
      progress_pct: 42,
      next_module: "Cell Structure",
      next_due: "Quiz 2 — Friday",
      completed: false,
    },
    {
      id: "PY101",
      title: "Python Fundamentals",
      instructor: "Prof. Rivera",
      progress_pct: 58,
      next_module: "Functions & Loops",
      next_due: "Assignment 2 — Monday",
      completed: false,
    },
  ],
  exams: [
    {
      id: "ex-bio-mid",
      title: "Biology Midterm",
      course_id: "BIO101",
      course: "Introduction to Biology",
      date: "May 28, 2026 · 10:00 AM",
      status: "Scheduled",
    },
  ],
  purchases: [
    { id: "p1", courseTitle: "Introduction to Biology", purchasedAt: "Jan 12, 2026", price: "$49.00" },
    { id: "p2", courseTitle: "Python Fundamentals", purchasedAt: "Feb 3, 2026", price: "$59.00" },
  ],
  certificates: [],
  announcements: [],
  recent_activity: [{ id: "a1", text: "Continued Biology module", at: "Today" }],
  progress: { BIO101: 42, PY101: 58 },
};

export const FALLBACK_JOHN: LmsStudentState = {
  student_id: "john-001",
  name: "John",
  email: "john.demo@smarted.test",
  role: "learner",
  profile_type: "new",
  courses: [],
  exams: [],
  purchases: [],
  certificates: [],
  announcements: [],
  recent_activity: [{ id: "a1", text: "Account created", at: "Today" }],
  progress: {},
};
