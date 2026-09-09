import { Link } from 'react-router-dom'

import { AppHeader } from '@/components/AppHeader'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'

export function DashboardPage() {
  return (
    <div className="min-h-svh bg-slate-50">
      <AppHeader />
      <main className="mx-auto max-w-3xl px-6 py-16">
        <div className="text-center">
          <h1 className="text-2xl font-semibold text-slate-900">Welcome</h1>
          <p className="mt-2 text-sm text-slate-500">Start a new interview, or catch up on your progress.</p>
          <div className="mt-8 flex justify-center gap-4">
            <Button asChild>
              <Link to="/resumes/upload">Upload resume</Link>
            </Button>
            <Button asChild variant="outline">
              <Link to="/job-descriptions/new">Paste job description</Link>
            </Button>
          </div>
        </div>

        <div className="mt-16 grid gap-4 sm:grid-cols-3">
          <Card>
            <CardHeader>
              <CardTitle>Analytics</CardTitle>
              <CardDescription>Skill breakdown and progress over time.</CardDescription>
            </CardHeader>
            <CardContent>
              <Button asChild variant="outline" className="w-full">
                <Link to="/analytics">View analytics</Link>
              </Button>
            </CardContent>
          </Card>
          <Card>
            <CardHeader>
              <CardTitle>Sessions</CardTitle>
              <CardDescription>Review your past interview sessions.</CardDescription>
            </CardHeader>
            <CardContent>
              <Button asChild variant="outline" className="w-full">
                <Link to="/sessions">View sessions</Link>
              </Button>
            </CardContent>
          </Card>
          <Card>
            <CardHeader>
              <CardTitle>Roadmap</CardTitle>
              <CardDescription>Your personalized learning plan.</CardDescription>
            </CardHeader>
            <CardContent>
              <Button asChild variant="outline" className="w-full">
                <Link to="/roadmap">View roadmap</Link>
              </Button>
            </CardContent>
          </Card>
        </div>
      </main>
    </div>
  )
}
