// Shapes actually produced by the extraction prompt
// (backend/app/prompts/resume_prompts.py). structured_data itself stays
// typed as Record<string, unknown> on the wire (ResumeOut in lib/api.ts);
// these are the narrowed shapes UI code casts into.
export interface ResumeExperienceEntry {
  title: string
  company: string
  start_date: string
  end_date: string
  description: string
}

export interface ResumeEducationEntry {
  institution: string
  degree: string
  field_of_study: string
  graduation_date: string
}

export interface ResumeProjectEntry {
  name: string
  description: string
  technologies: string[]
}

export interface ResumeStructuredData {
  skills?: string[]
  experience?: ResumeExperienceEntry[]
  education?: ResumeEducationEntry[]
  projects?: ResumeProjectEntry[]
}

export const emptyExperienceEntry: ResumeExperienceEntry = {
  title: '',
  company: '',
  start_date: '',
  end_date: '',
  description: '',
}

export const emptyEducationEntry: ResumeEducationEntry = {
  institution: '',
  degree: '',
  field_of_study: '',
  graduation_date: '',
}

export const emptyProjectEntry: ResumeProjectEntry = {
  name: '',
  description: '',
  technologies: [],
}
