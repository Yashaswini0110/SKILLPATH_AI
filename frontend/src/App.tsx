import { Navigate, Route, Routes } from "react-router-dom";
import { ProtectedRoute } from "./components/common/ProtectedRoute";
import { RoleProtectedRoute } from "./components/common/RoleProtectedRoute";
import { AppLayout } from "./components/layout/AppLayout";
import { AnalyticsPage } from "./pages/AnalyticsPage";
import { DashboardPage } from "./pages/DashboardPage";
import { LoginPage } from "./pages/LoginPage";
import { ProfilePage } from "./pages/ProfilePage";
import { RegisterPage } from "./pages/RegisterPage";
import { ResumePage } from "./pages/ResumePage";
import { RolesPage } from "./pages/RolesPage";
import { GapsPage } from "./pages/GapsPage";
import { MentorsPage } from "./pages/MentorsPage";
import { PathPage } from "./pages/PathPage";
import { AssessmentsPage } from "./pages/AssessmentsPage";
import { AssessmentTakePage } from "./pages/AssessmentTakePage";
import { AssistantPage } from "./pages/AssistantPage";
import { WhatIfPage } from "./pages/WhatIfPage";
import { PracticePage } from "./pages/PracticePage";
import { RecommendationsPage } from "./pages/RecommendationsPage";
import { ResourcesPage } from "./pages/ResourcesPage";
import { SkillProfilePage } from "./pages/SkillProfilePage";

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />
      <Route element={<ProtectedRoute />}>
        <Route element={<AppLayout />}>
          <Route path="/dashboard" element={<DashboardPage />} />
          <Route path="/profile" element={<ProfilePage />} />
          <Route path="/resume" element={<ResumePage />} />
          <Route path="/skills" element={<SkillProfilePage />} />
          <Route path="/twin" element={<Navigate to="/skills" replace />} />
          <Route path="/gaps" element={<GapsPage />} />
          <Route path="/graph" element={<Navigate to="/gaps?tab=graph" replace />} />
          <Route path="/resources" element={<ResourcesPage />} />
          <Route path="/recommendations" element={<RecommendationsPage />} />
          <Route path="/practice" element={<PracticePage />} />
          <Route path="/mentors" element={<MentorsPage />} />
          <Route path="/path" element={<PathPage />} />
          <Route path="/assessments/:assessmentId" element={<AssessmentTakePage />} />
          <Route path="/assessments" element={<AssessmentsPage />} />
          <Route path="/assistant" element={<AssistantPage />} />
          <Route path="/compare" element={<WhatIfPage />} />
          <Route path="/roles" element={<RolesPage />} />
          <Route element={<RoleProtectedRoute />}>
            <Route path="/analytics" element={<AnalyticsPage />} />
          </Route>
        </Route>
      </Route>
      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  );
}
