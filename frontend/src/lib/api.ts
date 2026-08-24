import { useAuthStore } from '@/store/authStore'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'

export class ApiError extends Error {
  status: number
  constructor(status: number, message: string) {
    super(message)
    this.status = status
  }
}

interface TokenResponse {
  access_token: string
  refresh_token: string
  token_type: string
}

async function rawRequest(path: string, init?: RequestInit): Promise<Response> {
  const isFormData = init?.body instanceof FormData
  return fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: {
      // FormData bodies must not set Content-Type manually - the browser
      // needs to add its own multipart boundary.
      ...(isFormData ? {} : { 'Content-Type': 'application/json' }),
      ...init?.headers,
    },
  })
}

async function tryRefresh(): Promise<boolean> {
  const { refreshToken, setTokens, clearTokens } = useAuthStore.getState()
  if (!refreshToken) return false

  const response = await rawRequest('/auth/refresh', {
    method: 'POST',
    body: JSON.stringify({ refresh_token: refreshToken }),
  })

  if (!response.ok) {
    clearTokens()
    return false
  }

  const tokens = (await response.json()) as TokenResponse
  setTokens({ accessToken: tokens.access_token, refreshToken: tokens.refresh_token })
  return true
}

export async function apiRequest<T>(path: string, init?: RequestInit, _retry = true): Promise<T> {
  const { accessToken } = useAuthStore.getState()

  const response = await rawRequest(path, {
    ...init,
    headers: {
      ...(accessToken ? { Authorization: `Bearer ${accessToken}` } : {}),
      ...init?.headers,
    },
  })

  if (response.status === 401 && _retry) {
    const refreshed = await tryRefresh()
    if (refreshed) {
      return apiRequest<T>(path, init, false)
    }
  }

  if (!response.ok) {
    const body = await response.json().catch(() => ({}))
    throw new ApiError(response.status, body.detail ?? `Request to ${path} failed`)
  }

  if (response.status === 204) {
    return undefined as T
  }
  return (await response.json()) as T
}

export async function signup(email: string, password: string): Promise<TokenResponse> {
  return apiRequest<TokenResponse>('/auth/signup', {
    method: 'POST',
    body: JSON.stringify({ email, password }),
  })
}

export async function login(email: string, password: string): Promise<TokenResponse> {
  return apiRequest<TokenResponse>('/auth/login', {
    method: 'POST',
    body: JSON.stringify({ email, password }),
  })
}

export async function logout(refreshToken: string): Promise<void> {
  await apiRequest<void>('/auth/logout', {
    method: 'POST',
    body: JSON.stringify({ refresh_token: refreshToken }),
  })
}

export async function bootstrapSession(): Promise<boolean> {
  return tryRefresh()
}

export interface ResumeOut {
  id: string
  status: string
  original_filename: string
  structured_data: Record<string, unknown> | null
  low_confidence_fields: string[] | null
  error_message: string | null
  created_at: string
}

export interface JobDescriptionOut {
  id: string
  status: string
  raw_text: string
  structured_data: Record<string, unknown> | null
  low_confidence_fields: string[] | null
  error_message: string | null
  created_at: string
}

export interface SkillGapOut {
  id: string
  resume_id: string
  job_description_id: string
  matched_skills: string[]
  missing_required_skills: string[]
  missing_preferred_skills: string[]
  match_score: number
  created_at: string
}

export async function uploadResume(file: File): Promise<ResumeOut> {
  const formData = new FormData()
  formData.append('file', file)
  return apiRequest<ResumeOut>('/resumes', { method: 'POST', body: formData })
}

export async function getResume(id: string): Promise<ResumeOut> {
  return apiRequest<ResumeOut>(`/resumes/${id}`)
}

export async function updateResume(id: string, structuredData: Record<string, unknown>): Promise<ResumeOut> {
  return apiRequest<ResumeOut>(`/resumes/${id}`, {
    method: 'PATCH',
    body: JSON.stringify({ structured_data: structuredData }),
  })
}

export async function createJobDescription(rawText: string): Promise<JobDescriptionOut> {
  return apiRequest<JobDescriptionOut>('/job-descriptions', {
    method: 'POST',
    body: JSON.stringify({ raw_text: rawText }),
  })
}

export async function getJobDescription(id: string): Promise<JobDescriptionOut> {
  return apiRequest<JobDescriptionOut>(`/job-descriptions/${id}`)
}

export async function updateJobDescription(
  id: string,
  structuredData: Record<string, unknown>,
): Promise<JobDescriptionOut> {
  return apiRequest<JobDescriptionOut>(`/job-descriptions/${id}`, {
    method: 'PATCH',
    body: JSON.stringify({ structured_data: structuredData }),
  })
}

export async function computeSkillGap(resumeId: string, jobDescriptionId: string): Promise<SkillGapOut> {
  return apiRequest<SkillGapOut>('/skill-gap', {
    method: 'POST',
    body: JSON.stringify({ resume_id: resumeId, job_description_id: jobDescriptionId }),
  })
}

export async function getSkillGap(id: string): Promise<SkillGapOut> {
  return apiRequest<SkillGapOut>(`/skill-gap/${id}`)
}

export type InterviewPlanFormat = 'quick' | 'standard' | 'thorough'

export interface InterviewPlanOut {
  id: string
  resume_id: string
  job_description_id: string
  skill_gap_analysis_id: string
  format: InterviewPlanFormat
  status: string
  question_count: number | null
  topic_mix: { topic: string; question_count: number }[] | null
  difficulty_min: number | null
  difficulty_max: number | null
  candidate_level: string | null
  rationale: string | null
  error_message: string | null
  created_at: string
}

export async function generateInterviewPlan(
  skillGapAnalysisId: string,
  format: InterviewPlanFormat,
): Promise<InterviewPlanOut> {
  return apiRequest<InterviewPlanOut>('/interview-plans', {
    method: 'POST',
    body: JSON.stringify({ skill_gap_analysis_id: skillGapAnalysisId, format }),
  })
}

export async function getInterviewPlan(id: string): Promise<InterviewPlanOut> {
  return apiRequest<InterviewPlanOut>(`/interview-plans/${id}`)
}

export type InterviewSessionStatus =
  | 'planned'
  | 'in_progress'
  | 'evaluating'
  | 'advancing'
  | 'complete'
  | 'abandoned'

export interface InterviewQuestion {
  turn_index: number
  topic: string
  difficulty: number
  question_text: string
}

export interface InterviewEvaluation {
  technical_score: number
  communication_score: number
  completeness_score: number
  rationale: string
}

export interface InterviewSummary {
  avg_technical_score: number
  avg_communication_score: number
  avg_completeness_score: number
  difficulty_path: number[]
}

export interface InterviewTurnOut {
  turn_index: number
  topic: string
  difficulty: number
  question_text: string
  answer_text: string | null
  evaluation: InterviewEvaluation | null
}

export interface InterviewSessionTranscript {
  session_id: string
  status: string
  total_questions: number
  turns: InterviewTurnOut[]
}

export interface StartInterviewSessionResult {
  session_id: string
  total_questions: number
  question: InterviewQuestion
}

// ---- WebSocket message shapes (/ws/interview-sessions/{id}) ----

export interface InterviewStateMessage {
  type: 'state'
  session_id: string
  interview_plan_id: string
  status: InterviewSessionStatus
  turn_index: number
  total_questions: number
  current_difficulty: number
  current_question: InterviewQuestion | null
  last_activity_at: string
  summary: InterviewSummary | null
}

export interface InterviewAnswerResultMessage {
  type: 'answer_result'
  evaluation: InterviewEvaluation
  status: 'in_progress' | 'complete'
  next_question: InterviewQuestion | null
  summary: InterviewSummary | null
}

export type InterviewWsErrorCode = 'bad_request' | 'llm_error' | 'inconsistent_state' | 'already_complete' | 'abandoned'

export interface InterviewErrorMessage {
  type: 'error'
  code: InterviewWsErrorCode
  detail: string
}

export type InterviewServerMessage = InterviewStateMessage | InterviewAnswerResultMessage | InterviewErrorMessage

export type InterviewClientMessage = { type: 'auth'; token: string } | { type: 'answer'; answer_text: string }

export async function startInterviewSession(planId: string): Promise<StartInterviewSessionResult> {
  return apiRequest<StartInterviewSessionResult>('/interview-sessions', {
    method: 'POST',
    body: JSON.stringify({ interview_plan_id: planId }),
  })
}

export async function getInterviewSessionTranscript(sessionId: string): Promise<InterviewSessionTranscript> {
  return apiRequest<InterviewSessionTranscript>(`/interview-sessions/${sessionId}`)
}

export function interviewSessionWsUrl(sessionId: string): string {
  return `${API_BASE_URL.replace(/^http/, 'ws')}/ws/interview-sessions/${sessionId}`
}
