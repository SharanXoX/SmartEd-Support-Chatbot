export type MockCourse = {
  id: string;
  title: string;
  instructor?: string;
  thumbnail?: string;
  progress_pct: number;
  next_module: string;
  next_due: string;
  completed?: boolean;
  exam_ids?: string[];
};

export type MockExam = {
  id: string;
  title: string;
  course_id?: string;
  course: string;
  date: string;
  status: "Scheduled" | "Completed" | "In review";
  score?: number | null;
};

export type MockCertificate = {
  id: string;
  course_id: string;
  course_title: string;
  issued_at: string;
};

export type MockPurchase = {
  id: string;
  course_id?: string;
  courseTitle: string;
  purchasedAt: string;
  price: string;
};

export type MockAnnouncement = {
  id: string;
  title: string;
  date: string;
  content: string;
};

export type MockActivity = {
  id: string;
  text: string;
  at: string;
};

export type LmsStudentState = {
  student_id: string;
  name: string;
  email: string;
  role: string;
  profile_type?: string;
  courses: MockCourse[];
  exams: MockExam[];
  purchases: MockPurchase[];
  certificates: MockCertificate[];
  announcements: MockAnnouncement[];
  recent_activity: MockActivity[];
  progress?: Record<string, number>;
};

export type ActiveUserSnapshot = {
  id: string;
  name: string;
  email: string;
  role: string;
  profile_type?: string;
  purchases: MockPurchase[];
  courses: MockCourse[];
  certificates: MockCertificate[];
  upcomingExams: MockExam[];
  progress: Record<string, number>;
};

export type LmsContextSnapshot = {
  current_route: string;
  current_page: string;
  student_id: string;
  activeUser: ActiveUserSnapshot;
  student: { student_id: string; name: string; email: string; role: string };
  courses: MockCourse[];
  purchases: MockPurchase[];
  upcoming_exams: MockExam[];
  recent_activity: MockActivity[];
  available_features: string[];
  available_routes: Record<string, string>;
  certificates_count: number;
  has_enrolled_courses: boolean;
  has_purchases: boolean;
};

export type StudentProfileOption = {
  id: string;
  name: string;
  profile_type: string;
};
