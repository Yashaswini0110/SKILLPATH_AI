import { api } from "./api";
import type {
  APIResponse,
  AuthPayload,
  Course,
  Education,
  EmployeeProfile,
  EmployeeSkill,
  Experience,
  GapAnalysis,
  GraphSkillView,
  GraphStatus,
  JobDescriptionDetail,
  JobDescriptionSummary,
  LearningPath,
  Mentor,
  MentorMatchList,
  PathMethod,
  PracticePairList,
  Project,
  RecommendationList,
  RecMethod,
  ResumeDetail,
  ResumeSummary,
  Skill,
  SkillProfile,
  SkillResolveResponse,
  TargetRole,
  TargetRoleDetail,
  User,
  UserRole,
  AssessmentAttempt,
  AssessmentDetail,
  AssessmentSummary,
  AssistantTurn,
  AnalyticsSnapshot,
  PagePublic,
  TwinSnapshot,
  WhatIfSimulation,
} from "../types/api";

export async function registerAccount(payload: {
  email: string;
  password: string;
  full_name: string;
  role: UserRole;
}): Promise<AuthPayload> {
  const { data } = await api.post<APIResponse<AuthPayload>>("/api/v1/auth/register", payload);
  return data.data;
}

export async function loginAccount(payload: {
  email: string;
  password: string;
}): Promise<AuthPayload> {
  const { data } = await api.post<APIResponse<AuthPayload>>("/api/v1/auth/login", payload);
  return data.data;
}

export async function logoutAccount(refreshToken: string | null): Promise<void> {
  await api.post("/api/v1/auth/logout", { refresh_token: refreshToken });
}

export async function fetchMe(): Promise<User> {
  const { data } = await api.get<APIResponse<User>>("/api/v1/auth/me");
  return data.data;
}

export async function fetchProfile(): Promise<EmployeeProfile> {
  const { data } = await api.get<APIResponse<EmployeeProfile>>("/api/v1/employees/me");
  return data.data;
}

export async function updateProfile(payload: Record<string, unknown>): Promise<EmployeeProfile> {
  const { data } = await api.put<APIResponse<EmployeeProfile>>("/api/v1/employees/me", payload);
  return data.data;
}

export async function addEducation(payload: Record<string, unknown>): Promise<Education> {
  const { data } = await api.post<APIResponse<Education>>(
    "/api/v1/employees/me/education",
    payload,
  );
  return data.data;
}

export async function deleteEducation(id: string): Promise<void> {
  await api.delete(`/api/v1/employees/me/education/${id}`);
}

export async function addExperience(payload: Record<string, unknown>): Promise<Experience> {
  const { data } = await api.post<APIResponse<Experience>>(
    "/api/v1/employees/me/experience",
    payload,
  );
  return data.data;
}

export async function deleteExperience(id: string): Promise<void> {
  await api.delete(`/api/v1/employees/me/experience/${id}`);
}

export async function fetchSkills(category?: string): Promise<Skill[]> {
  const { data } = await api.get<APIResponse<PagePublic<Skill>>>("/api/v1/skills", {
    params: category ? { category } : undefined,
  });
  return data.data.items;
}

export async function resolveSkills(mentions: string[]): Promise<SkillResolveResponse> {
  const { data } = await api.post<APIResponse<SkillResolveResponse>>(
    "/api/v1/skills/resolve",
    { mentions },
  );
  return data.data;
}

export async function addSkill(payload: {
  skill_id: string;
  current_level: number;
}): Promise<EmployeeSkill> {
  const { data } = await api.post<APIResponse<EmployeeSkill>>(
    "/api/v1/employees/me/skills",
    payload,
  );
  return data.data;
}

export async function deleteSkill(id: string): Promise<void> {
  await api.delete(`/api/v1/employees/me/skills/${id}`);
}

export async function fetchRoles(): Promise<TargetRole[]> {
  const { data } = await api.get<APIResponse<PagePublic<TargetRole>>>("/api/v1/roles");
  return data.data.items;
}

export async function fetchRole(id: string): Promise<TargetRoleDetail> {
  const { data } = await api.get<APIResponse<TargetRoleDetail>>(`/api/v1/roles/${id}`);
  return data.data;
}

export async function fetchResumes(): Promise<ResumeSummary[]> {
  const { data } = await api.get<APIResponse<ResumeSummary[]>>("/api/v1/employees/me/resumes");
  return data.data;
}

export async function fetchResume(id: string): Promise<ResumeDetail> {
  const { data } = await api.get<APIResponse<ResumeDetail>>(`/api/v1/employees/me/resumes/${id}`);
  return data.data;
}

export async function uploadResume(file: File): Promise<ResumeDetail> {
  const form = new FormData();
  form.append("file", file);
  const { data } = await api.post<APIResponse<ResumeDetail>>("/api/v1/employees/me/resumes", form);
  return data.data;
}

export async function fetchJobDescriptions(): Promise<JobDescriptionSummary[]> {
  const { data } = await api.get<APIResponse<JobDescriptionSummary[]>>("/api/v1/job-descriptions");
  return data.data;
}

export async function fetchJobDescription(id: string): Promise<JobDescriptionDetail> {
  const { data } = await api.get<APIResponse<JobDescriptionDetail>>(`/api/v1/job-descriptions/${id}`);
  return data.data;
}

export async function analyzeJobDescription(payload: {
  title?: string;
  text: string;
}): Promise<JobDescriptionDetail> {
  const { data } = await api.post<APIResponse<JobDescriptionDetail>>("/api/v1/job-descriptions", payload);
  return data.data;
}

export async function uploadJobDescription(file: File, title?: string): Promise<JobDescriptionDetail> {
  const form = new FormData();
  form.append("file", file);
  if (title) form.append("title", title);
  const { data } = await api.post<APIResponse<JobDescriptionDetail>>(
    "/api/v1/job-descriptions/upload",
    form,
  );
  return data.data;
}

export async function fetchSkillProfile(): Promise<SkillProfile> {
  const { data } = await api.get<APIResponse<SkillProfile>>("/api/v1/employees/me/skill-profile");
  return data.data;
}

export async function fetchGapAnalysis(params?: {
  role_id?: string;
  job_description_id?: string;
}): Promise<GapAnalysis> {
  const { data } = await api.get<APIResponse<GapAnalysis>>("/api/v1/gap-analysis", {
    params,
  });
  return data.data;
}

export async function fetchCourses(skillId?: string): Promise<Course[]> {
  const { data } = await api.get<APIResponse<PagePublic<Course>>>("/api/v1/courses", {
    params: skillId ? { skill_id: skillId } : undefined,
  });
  return data.data.items;
}

export async function fetchProjects(skillId?: string): Promise<Project[]> {
  const { data } = await api.get<APIResponse<PagePublic<Project>>>("/api/v1/projects", {
    params: skillId ? { skill_id: skillId } : undefined,
  });
  return data.data.items;
}

export async function fetchMentors(skillId?: string): Promise<Mentor[]> {
  const { data } = await api.get<APIResponse<PagePublic<Mentor>>>("/api/v1/mentors", {
    params: skillId ? { skill_id: skillId } : undefined,
  });
  return data.data.items;
}

export async function fetchRecommendations(params: {
  resource: "courses" | "projects" | "mentors";
  method: RecMethod;
}): Promise<RecommendationList> {
  const { data } = await api.get<APIResponse<RecommendationList>>(
    `/api/v1/recommendations/${params.resource}`,
    { params: { method: params.method } },
  );
  return data.data;
}

export async function fetchPracticePairs(): Promise<PracticePairList> {
  const { data } = await api.get<APIResponse<PracticePairList>>(
    "/api/v1/recommendations/practice-pairs",
  );
  return data.data;
}

export async function fetchMentorMatches(): Promise<MentorMatchList> {
  const { data } = await api.get<APIResponse<MentorMatchList>>(
    "/api/v1/recommendations/mentor-matches",
  );
  return data.data;
}

export async function fetchLearningPath(
  method: PathMethod = "ORTOOLS",
): Promise<LearningPath> {
  const { data } = await api.get<APIResponse<LearningPath>>("/api/v1/learning-paths", {
    params: { method },
  });
  return data.data;
}

export async function fetchGraphStatus(): Promise<GraphStatus> {
  const { data } = await api.get<APIResponse<GraphStatus>>("/api/v1/graph/status");
  return data.data;
}

export async function fetchGraphSkill(skillId: string): Promise<GraphSkillView> {
  const { data } = await api.get<APIResponse<GraphSkillView>>(
    `/api/v1/graph/skills/${skillId}`,
  );
  return data.data;
}

export async function fetchAssessments(skillId?: string): Promise<AssessmentSummary[]> {
  const { data } = await api.get<APIResponse<PagePublic<AssessmentSummary>>>(
    "/api/v1/assessments",
    { params: skillId ? { skill_id: skillId } : undefined },
  );
  return data.data.items;
}

export async function fetchAssessment(id: string): Promise<AssessmentDetail> {
  const { data } = await api.get<APIResponse<AssessmentDetail>>(`/api/v1/assessments/${id}`);
  return data.data;
}

export async function submitAssessment(
  id: string,
  answers: { question_id: string; selected_index: number | null }[],
): Promise<AssessmentAttempt> {
  const { data } = await api.post<APIResponse<AssessmentAttempt>>(
    `/api/v1/assessments/${id}/attempts`,
    { answers },
  );
  return data.data;
}

export async function askAssistant(question: string): Promise<AssistantTurn> {
  const { data } = await api.post<APIResponse<AssistantTurn>>("/api/v1/assistant/ask", {
    question,
  });
  return data.data;
}

export async function fetchAssistantTurns(): Promise<AssistantTurn[]> {
  const { data } = await api.get<APIResponse<AssistantTurn[]>>("/api/v1/assistant/turns");
  return data.data;
}

export async function fetchWhatIf(roleIds: string[]): Promise<WhatIfSimulation> {
  const params = new URLSearchParams();
  for (const id of roleIds) {
    params.append("role_ids", id);
  }
  const { data } = await api.get<APIResponse<WhatIfSimulation>>("/api/v1/what-if", {
    params,
  });
  return data.data;
}

export async function fetchTwin(params?: {
  role_id?: string;
  job_description_id?: string;
}): Promise<TwinSnapshot> {
  const { data } = await api.get<APIResponse<TwinSnapshot>>("/api/v1/twin", {
    params,
  });
  return data.data;
}

export async function fetchAnalytics(department?: string): Promise<AnalyticsSnapshot> {
  const { data } = await api.get<APIResponse<AnalyticsSnapshot>>("/api/v1/analytics", {
    params: department ? { department } : undefined,
  });
  return data.data;
}
