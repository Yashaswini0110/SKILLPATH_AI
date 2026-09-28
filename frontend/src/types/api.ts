export type UserRole =
  | "EMPLOYEE"
  | "MANAGER"
  | "MENTOR"
  | "HR_ADMIN"
  | "SYSTEM_ADMIN";

export interface APIResponse<T> {
  data: T;
  message: string | null;
}

export interface PagePublic<T> {
  items: T[];
  page: number;
  page_size: number;
  total: number;
  total_pages: number;
  sort: string | null;
  order: "asc" | "desc";
}

export interface APIErrorBody {
  error: {
    code: string;
    message: string;
    details: unknown[];
  };
}

export interface User {
  id: string;
  email: string;
  full_name: string;
  role: UserRole;
  is_active: boolean;
}

export interface TokenPair {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

export interface AuthPayload {
  tokens: TokenPair;
  user: User;
}

export interface Skill {
  id: string;
  name: string;
  canonical_name: string;
  category: string;
  description: string | null;
  difficulty: number;
  aliases: string[];
}

export type SkillMatchType = "exact" | "alias" | "collision" | "unmatched";

export interface SkillResolveItem {
  raw: string;
  skill_id: string | null;
  canonical_name: string | null;
  confidence: number;
  matched_term: string | null;
  match_type: SkillMatchType;
}

export interface SkillResolveResponse {
  results: SkillResolveItem[];
}

export interface TargetRole {
  id: string;
  title: string;
  category: string;
  description: string | null;
}

export type RequirementType = "REQUIRED" | "PREFERRED" | "MENTIONED";

export interface RequirementWeights {
  required: number;
  preferred: number;
  mentioned: number;
}

export interface RoleSkill {
  skill: Skill;
  required_level: number;
  importance: number;
  criticality: number;
  requirement: RequirementType;
}

export interface TargetRoleDetail extends TargetRole {
  weights: RequirementWeights;
  skills: RoleSkill[];
}

export interface Education {
  id: string;
  degree: string;
  institution: string;
  field_of_study: string | null;
  start_year: number | null;
  end_year: number | null;
  description: string | null;
}

export interface Experience {
  id: string;
  company: string;
  role_title: string;
  description: string | null;
  start_date: string;
  end_date: string | null;
  is_current: boolean;
}

export interface EmployeeSkill {
  id: string;
  current_level: number;
  confidence: number;
  source_type: string;
  inferred: boolean;
  skill: Skill;
}

export interface Completeness {
  score: number;
  completed_items: number;
  total_items: number;
  breakdown: {
    job_title: boolean;
    department: boolean;
    years_experience: boolean;
    education: boolean;
    experience: boolean;
    skills: boolean;
    target_role: boolean;
    learning_preferences: boolean;
  };
}

export interface EmployeeProfile {
  id: string;
  user_id: string;
  full_name: string;
  email: string;
  role: UserRole;
  job_title: string | null;
  department: string | null;
  years_experience: number | null;
  available_hours_per_week: number;
  learning_preferences: { formats: string[]; pace: string | null } | null;
  target_role: TargetRole | null;
  completeness: Completeness;
  education: Education[];
  experience: Experience[];
  skills: EmployeeSkill[];
}

export interface ResumeSummary {
  id: string;
  original_filename: string;
  content_type: string;
  status: string;
  created_at: string;
  skill_count: number;
}

export interface ExtractedSkill {
  id: string;
  skill: Skill;
  extracted_level: number;
  confidence: number;
  reliability: number;
  strength: number;
  source_type: string;
  inferred: boolean;
  evidence_snippet: string | null;
  section: string | null;
  match_type: string | null;
}

export interface ResumeDetail extends ResumeSummary {
  extracted_text: string | null;
  error_message: string | null;
  skills: ExtractedSkill[];
}

export interface JobDescriptionSummary {
  id: string;
  title: string;
  source_type: "PASTE" | "FILE";
  original_filename: string | null;
  status: string;
  created_at: string;
  skill_count: number;
}

export interface JobDescriptionSkill {
  id: string;
  skill: Skill;
  requirement: RequirementType;
  importance: number;
  required_level: number;
  match_type: string;
  mention_count: number;
}

export interface JobDescriptionDetail extends JobDescriptionSummary {
  extracted_text: string | null;
  error_message: string | null;
  weights: RequirementWeights;
  skills: JobDescriptionSkill[];
}

export type ConfidenceLabel = "HIGH" | "MEDIUM" | "LOW";

export interface SkillEvidence {
  id: string | null;
  source_type: string;
  extracted_level: number;
  reliability: number;
  strength: number;
  recency: number;
  inferred: boolean;
}

export interface AggregatedSkill {
  skill: Skill;
  current_level: number;
  confidence: number;
  confidence_label: ConfidenceLabel;
  conflict: boolean;
  variance: number;
  recommend_assessment: boolean;
  inferred_only: boolean;
  evidence: SkillEvidence[];
}

export interface SkillProfile {
  skill_count: number;
  conflict_count: number;
  conflict_variance_threshold: number;
  source_reliability: Record<string, number>;
  skills: AggregatedSkill[];
}

export type GapPriority = "CRITICAL" | "HIGH" | "MEDIUM" | "LOW" | "NONE";

export interface GapTarget {
  type: "ROLE" | "JOB_DESCRIPTION";
  id: string;
  title: string;
}

export interface GapItem {
  skill: Skill;
  required_level: number | string;
  current_level: number | string;
  gap_basic: number | string;
  gap: number | string;
  priority: GapPriority;
  importance: number | string;
  criticality: number | string;
  confidence: number | string;
  evidence_strength: number | string;
  requirement: RequirementType;
  inferred_only: boolean;
  conflict: boolean;
}

export interface GapAnalysis {
  target: GapTarget;
  gap_count: number;
  critical_count: number;
  high_count: number;
  medium_count: number;
  low_count: number;
  none_count: number;
  gaps: GapItem[];
}

export interface ResourceSkill {
  skill: Skill;
  level: number;
}

export interface Course {
  id: string;
  title: string;
  provider: string;
  description: string;
  difficulty: number;
  duration_hours: number;
  format: string;
  url: string;
  rating: number | string;
  skills: ResourceSkill[];
}

export interface Project {
  id: string;
  title: string;
  description: string;
  difficulty: number;
  duration_hours: number;
  technologies: string[];
  deliverables: string[];
  skills: ResourceSkill[];
}

export interface Mentor {
  id: string;
  name: string;
  title: string;
  bio: string;
  years_experience: number;
  available_hours_per_month: number;
  max_mentees: number;
  domains: string[];
  skills: ResourceSkill[];
}

export type RecMethod =
  | "POPULARITY"
  | "CONTENT"
  | "SEMANTIC"
  | "KG"
  | "HYBRID";

export interface MatchedGapSkill {
  skill: Skill;
  gap: number | string;
  priority: string;
}

export interface ExplanationFact {
  key: string;
  text: string;
  value?: string | number | null;
}

export interface Explanation {
  facts: ExplanationFact[];
  verbalization: string;
}

export interface RecommendationItem {
  rank: number;
  score: number | string;
  components: Record<string, number | string | null>;
  matched_skills: MatchedGapSkill[];
  reason: string;
  explanation: Explanation;
  course: Course | null;
  project: Project | null;
  mentor: Mentor | null;
}

export interface RecommendationList {
  batch_id: string;
  method: RecMethod;
  resource_type: "COURSE" | "PROJECT" | "MENTOR";
  encoder: string | null;
  target: GapTarget;
  gap_skills: MatchedGapSkill[];
  items: RecommendationItem[];
  weights?: Record<string, number> | null;
}

export interface PracticePair {
  rank: number;
  score: number | string;
  skill: Skill;
  gap: number | string;
  priority: string;
  current_level: number | string;
  required_level: number | string;
  course: Course;
  project: Project;
  components: Record<string, unknown>;
  reason: string;
  explanation: Explanation;
}

export interface PracticePairList {
  batch_id: string;
  target: GapTarget;
  weights: Record<string, number>;
  items: PracticePair[];
}

export interface MentorWhy {
  matched_gap_count: number;
  top_gap_count: number;
  matched_skills: Skill[];
  available_hours_per_month: number;
  open_mentee_slots: number;
  domains: string[];
}

export interface MentorMatchItem {
  rank: number;
  score: number | string;
  mentor: Mentor;
  components: Record<string, unknown>;
  why: MentorWhy;
  reason: string;
  explanation: Explanation;
}

export interface MentorMatchList {
  batch_id: string;
  target: GapTarget;
  weights: Record<string, number>;
  gap_skills: MatchedGapSkill[];
  items: MentorMatchItem[];
}

export type PathMethod = "ORTOOLS" | "GREEDY" | "TOPOLOGICAL";

export interface PathMethodScore {
  method: PathMethod | string;
  selected_count: number;
  total_hours: number;
  estimated_weeks: number;
  skill_coverage: number;
  prerequisite_violation_count: number;
  hours_violation_count: number;
  path_efficiency: number;
}

export type PathStage = "FOUNDATION" | "CORE" | "ADVANCED" | string;

export interface LearningPathStep {
  position: number;
  skill: Skill;
  kind: string;
  stage: PathStage;
  status: string;
  difficulty: number;
  reason: string;
  blocked_by: string[];
  course: Course | null;
  project: Project | null;
  duration_hours: number;
  week_start: number;
  week_end: number;
  assessment_id: string | null;
  why: Record<string, unknown>;
  explanation: Explanation;
}

export interface PathAdaptation {
  skill: string;
  action: "SKIP" | "REFRESHER" | string;
  percent: number;
  extra_hours: number;
  reason: string;
}

export interface LearningPath {
  id: string;
  method: PathMethod | string;
  prerequisite_violation_count: number;
  hours_violation_count: number;
  duplicate_resource_count: number;
  hours_per_week: number;
  deadline_weeks: number;
  capacity_hours: number;
  total_hours: number;
  estimated_weeks: number;
  skill_coverage: number;
  path_efficiency: number;
  target: GapTarget;
  gap_skills: MatchedGapSkill[];
  skipped_foundations: string[];
  adaptations: PathAdaptation[];
  comparison: PathMethodScore[];
  reason: string;
  steps: LearningPathStep[];
  edges: string[][];
}

export interface GraphRelatedSkill {
  skill: Skill;
  relation: string;
}

export interface GraphEdge {
  source: Skill;
  target: Skill;
}

export interface GraphSkillView {
  skill: Skill;
  prerequisites: Skill[];
  chain: Skill[];
  layers: Skill[][];
  edges: GraphEdge[];
  related: GraphRelatedSkill[];
  courses: Course[];
  projects: Project[];
  mentors: Mentor[];
}

export interface GraphStatus {
  connected: boolean;
  acyclic: boolean;
  cycle_count: number;
  cycles: string[][];
  nodes: Record<string, number>;
}

export interface AssessmentSummary {
  id: string;
  skill: Skill;
  title: string;
  assessment_type: string;
  question_count: number;
  pass_score: number;
  latest_percent: number | null;
  latest_passed: boolean | null;
  attempt_count: number;
}

export interface AssessmentQuestion {
  id: string;
  position: number;
  prompt: string;
  choices: string[];
}

export interface AssessmentDetail {
  id: string;
  skill: Skill;
  title: string;
  assessment_type: string;
  pass_score: number;
  questions: AssessmentQuestion[];
}

export interface AssessmentAnswerResult {
  question_id: string;
  position: number;
  prompt: string;
  selected_index: number | null;
  correct_index: number;
  is_correct: boolean;
  explanation: string | null;
}

export interface AssessmentAttempt {
  id: string;
  assessment_id: string;
  skill: Skill;
  percent: number;
  correct_count: number;
  total: number;
  extracted_level: number;
  passed: boolean;
  path_effect: "SKIP" | "REFRESHER" | string | null;
  answers: AssessmentAnswerResult[];
}

export interface AssistantSource {
  source_type: string;
  title: string;
  text: string;
  source_id: string | null;
}

export interface AssistantTurn {
  id: string;
  question: string;
  answer: string;
  sources: AssistantSource[];
  used_llm: boolean;
  unavailable: boolean;
}

export interface WhatIfMissingSkill {
  skill: string;
  priority: string;
  current_level: number;
  required_level: number;
}

export interface WhatIfScenario {
  role: TargetRole;
  is_current: boolean;
  skill_count: number;
  covered_count: number;
  coverage: number;
  open_gap_count: number;
  missing_skills: WhatIfMissingSkill[];
  estimated_hours: number;
  estimated_weeks: number;
  path_skills: string[];
  required_projects: string[];
  mentor_count: number;
  mentor_names: string[];
}

export interface WhatIfSimulation {
  current_target: { type: string; id: string; title: string } | null;
  hours_per_week: number;
  disclaimer: string;
  scenarios: WhatIfScenario[];
}

export type TwinTrend = "IMPROVING" | "STABLE" | "DECLINING" | "INSUFFICIENT_DATA";

export interface TwinEvidenceSource {
  source_type: string;
  present: boolean;
  level: number | string | null;
  inferred: boolean;
}

export interface TwinHistoryPoint {
  at: string;
  source_type: string;
  level: number | string;
  inferred: boolean;
}

export interface TwinSkill {
  skill: Skill;
  current_level: number | string;
  required_level: number | string | null;
  gap_basic: number | string | null;
  gap: number | string | null;
  priority: GapPriority | null;
  requirement: RequirementType | null;
  confidence: number | string;
  confidence_label: ConfidenceLabel;
  conflict: boolean;
  inferred_only: boolean;
  recommend_assessment: boolean;
  in_target: boolean;
  evidence_sources: TwinEvidenceSource[];
  history: TwinHistoryPoint[];
  trend: TwinTrend;
}

export interface TwinSnapshot {
  target: GapTarget;
  disclaimer: string;
  skill_count: number;
  open_gap_count: number;
  conflict_count: number;
  github_collected: boolean;
  skills: TwinSkill[];
}

export interface AnalyticsSkill {
  id: string;
  canonical_name: string;
  category: string;
}

export interface HeatmapRow {
  skill: AnalyticsSkill;
  band_1: number;
  band_2: number;
  band_3: number;
  band_4: number;
  band_5: number;
  missing_count: number;
}

export interface GapAggregate {
  skill: AnalyticsSkill;
  employees_with_gap: number;
  avg_gap: number;
  critical_count: number;
  high_count: number;
}

export interface TrainingPriority {
  skill: AnalyticsSkill;
  rank: number;
  employees_with_gap: number;
  avg_gap: number;
  course_count: number;
  project_count: number;
}

export interface LearningProgress {
  employees_with_attempts: number;
  total_attempts: number;
  pass_rate: number;
  employees_with_paths: number;
  avg_path_coverage: number;
}

export interface FrameworkAdoption {
  role_id: string;
  title: string;
  employees_targeting: number;
}

export interface DepartmentSlice {
  department: string;
  employee_count: number;
}

export interface AnalyticsSnapshot {
  scope: { type: string; label: string };
  disclaimer: string;
  employee_count: number;
  with_target_role_count: number;
  avg_completeness: number;
  heatmap: HeatmapRow[];
  top_gaps: GapAggregate[];
  training_priorities: TrainingPriority[];
  learning_progress: LearningProgress;
  frameworks: FrameworkAdoption[];
  departments: DepartmentSlice[];
  github_collected: boolean;
}
