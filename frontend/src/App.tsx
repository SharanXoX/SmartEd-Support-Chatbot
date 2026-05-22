import { Navigate, Route, Routes } from "react-router-dom";
import LmsDemoLayout from "./layouts/LmsDemoLayout";
import AdminDashboard from "./pages/AdminDashboard";
import DemoAnnouncements from "./pages/demo/DemoAnnouncements";
import DemoCalendar from "./pages/demo/DemoCalendar";
import DemoCertifications from "./pages/demo/DemoCertifications";
import DemoCourseDetail from "./pages/demo/DemoCourseDetail";
import DemoCourses from "./pages/demo/DemoCourses";
import DemoDashboard from "./pages/demo/DemoDashboard";
import DemoExams from "./pages/demo/DemoExams";
import DemoHelp from "./pages/demo/DemoHelp";
import DemoPlaceholderPage from "./pages/demo/DemoPlaceholderPage";
import DemoPolicy from "./pages/demo/DemoPolicy";
import DemoProfile from "./pages/demo/DemoProfile";
import DemoPurchases from "./pages/demo/DemoPurchases";
import DemoSettings from "./pages/demo/DemoSettings";

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Navigate to="/demo/dashboard" replace />} />
      <Route path="/demo" element={<LmsDemoLayout />}>
        <Route path="dashboard" element={<DemoDashboard />} />
        <Route path="announcements" element={<DemoAnnouncements />} />
        <Route path="courses" element={<DemoCourses />} />
        <Route path="course/:courseId" element={<DemoCourseDetail />} />
        <Route path="calendar" element={<DemoCalendar />} />
        <Route path="exams" element={<DemoExams />} />
        <Route path="certifications" element={<DemoCertifications />} />
        <Route path="certificates" element={<Navigate to="/demo/certifications" replace />} />
        <Route path="purchases" element={<DemoPurchases />} />
        <Route path="profile" element={<DemoProfile />} />
        <Route path="settings" element={<DemoSettings />} />
        <Route path="help" element={<DemoHelp />} />
        {/* Legacy routes preserved for support flows & deep links */}
        <Route
          path="assignments"
          element={
            <DemoPlaceholderPage
              title="Assignments"
              description="View due dates, instructions, and upload your work. Use the support assistant if you need step-by-step help submitting."
              hint='Try asking: "How do I submit an assignment?"'
            />
          }
        />
        <Route
          path="assignment-upload"
          element={
            <DemoPlaceholderPage
              title="Upload Assignment"
              description="Attach your file (PDF, DOCX, or ZIP), review the checklist, then submit before the deadline."
            />
          }
        />
        <Route
          path="quizzes"
          element={
            <DemoPlaceholderPage
              title="Quizzes"
              description="Timed and practice quizzes appear here. Open a quiz to see attempts remaining and instructions."
            />
          }
        />
        <Route path="notes" element={<Navigate to="/demo/courses" replace />} />
        <Route path="progress" element={<Navigate to="/demo/profile" replace />} />
        <Route path="policy/:policyId" element={<DemoPolicy />} />
      </Route>
      <Route path="/admin" element={<AdminDashboard />} />
      <Route path="*" element={<Navigate to="/demo/dashboard" replace />} />
    </Routes>
  );
}
