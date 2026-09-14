import type { ResumeStructuredData } from '@/types/resume'

interface JobDescriptionStructuredData {
  required_skills?: string[]
  preferred_skills?: string[]
  seniority_level?: string
}

const GENERIC_GAP_MESSAGE =
  "We didn't find much detail here — consider adding any missing skills or experience for a better-tailored interview."

// Deliberately about genuine gaps, not nitpicking: a resume with real
// experience but zero side projects is normal and shouldn't be flagged.
export function getResumeGapMessage(data: ResumeStructuredData | null | undefined): string | null {
  if (!data) return null

  const skills = data.skills ?? []
  const experience = data.experience ?? []
  const education = data.education ?? []
  const projects = data.projects ?? []

  const isSparse =
    skills.length < 3 || experience.length === 0 || education.length === 0 || (projects.length === 0 && experience.length === 0)

  return isSparse ? GENERIC_GAP_MESSAGE : null
}

export function getJdGapMessage(data: JobDescriptionStructuredData | null | undefined): string | null {
  if (!data) return null

  const requiredSkills = data.required_skills ?? []
  const isSparse = requiredSkills.length === 0 || !data.seniority_level?.trim()

  return isSparse ? GENERIC_GAP_MESSAGE : null
}
