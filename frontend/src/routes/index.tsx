import { createBrowserRouter, Navigate } from 'react-router-dom'

import { ProtectedRoute } from '@/components/ProtectedRoute'
import { AppLayout } from '@/components/AppLayout'
import { LoginPage } from '@/pages/Login'
import { SignupPage } from '@/pages/Signup'
import { DashboardPage } from '@/pages/Dashboard'
import { ResumeDetailPage } from '@/pages/ResumeDetail'
import { JobDescriptionDetailPage } from '@/pages/JobDescriptionDetail'
import { StartInterviewPage } from '@/pages/StartInterview'
import { PreSessionCheckPage } from '@/pages/PreSessionCheck'
import { LiveInterviewPage } from '@/pages/LiveInterview'
import { AnalyticsPage } from '@/pages/Analytics'
import { SessionHistoryPage } from '@/pages/SessionHistory'
import { SessionDetailPage } from '@/pages/SessionDetail'
import { RoadmapPage } from '@/pages/Roadmap'

export const router = createBrowserRouter([
  { path: '/', element: <Navigate to="/dashboard" replace /> },
  { path: '/login', element: <LoginPage /> },
  { path: '/signup', element: <SignupPage /> },
  {
    element: <ProtectedRoute />,
    children: [
      {
        element: <AppLayout />,
        children: [
          { path: '/dashboard', element: <DashboardPage /> },
          { path: '/resumes/:resumeId', element: <ResumeDetailPage /> },
          { path: '/job-descriptions/:jdId', element: <JobDescriptionDetailPage /> },
          { path: '/start-interview', element: <StartInterviewPage /> },
          { path: '/interview-sessions/:sessionId/check', element: <PreSessionCheckPage /> },
          { path: '/interview-sessions/:sessionId/live', element: <LiveInterviewPage /> },
          { path: '/interview-sessions/:sessionId', element: <SessionDetailPage /> },
          { path: '/analytics', element: <AnalyticsPage /> },
          { path: '/sessions', element: <SessionHistoryPage /> },
          { path: '/roadmap', element: <RoadmapPage /> },
        ],
      },
    ],
  },
])
