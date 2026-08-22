import { createBrowserRouter, Navigate } from 'react-router-dom'

import { ProtectedRoute } from '@/components/ProtectedRoute'
import { LoginPage } from '@/pages/Login'
import { SignupPage } from '@/pages/Signup'
import { DashboardPage } from '@/pages/Dashboard'
import { ResumeUploadPage } from '@/pages/ResumeUpload'
import { ResumeReviewPage } from '@/pages/ResumeReview'
import { JobDescriptionCreatePage } from '@/pages/JobDescriptionCreate'
import { JobDescriptionReviewPage } from '@/pages/JobDescriptionReview'
import { InterviewPlanCreatePage } from '@/pages/InterviewPlanCreate'
import { InterviewPlanReviewPage } from '@/pages/InterviewPlanReview'

export const router = createBrowserRouter([
  { path: '/', element: <Navigate to="/dashboard" replace /> },
  { path: '/login', element: <LoginPage /> },
  { path: '/signup', element: <SignupPage /> },
  {
    element: <ProtectedRoute />,
    children: [
      { path: '/dashboard', element: <DashboardPage /> },
      { path: '/resumes/upload', element: <ResumeUploadPage /> },
      { path: '/resumes/:resumeId/review', element: <ResumeReviewPage /> },
      { path: '/job-descriptions/new', element: <JobDescriptionCreatePage /> },
      { path: '/job-descriptions/:jdId/review', element: <JobDescriptionReviewPage /> },
      { path: '/interview-plans/new', element: <InterviewPlanCreatePage /> },
      { path: '/interview-plans/:planId/review', element: <InterviewPlanReviewPage /> },
    ],
  },
])
