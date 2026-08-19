import { useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { useCreateJobDescription } from '@/hooks/useJobDescription'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Textarea } from '@/components/ui/textarea'

export function JobDescriptionCreatePage() {
  const navigate = useNavigate()
  const [rawText, setRawText] = useState('')
  const create = useCreateJobDescription()

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault()
    if (!rawText.trim()) return
    const jd = await create.mutateAsync(rawText)
    navigate(`/job-descriptions/${jd.id}/review`)
  }

  return (
    <div className="min-h-svh bg-slate-50">
      <main className="mx-auto max-w-xl px-6 py-16">
        <Card>
          <CardHeader>
            <CardTitle>Paste a job description</CardTitle>
            <CardDescription>We'll extract required and preferred skills, plus seniority level.</CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="flex flex-col gap-4">
              <Textarea
                value={rawText}
                onChange={(event) => setRawText(event.target.value)}
                placeholder="Paste the full job description here..."
                rows={12}
              />
              {create.isError && <p className="text-sm text-red-600">Analysis failed. Please try again.</p>}
              <Button type="submit" disabled={!rawText.trim() || create.isPending}>
                {create.isPending ? 'Analyzing...' : 'Analyze'}
              </Button>
            </form>
          </CardContent>
        </Card>
      </main>
    </div>
  )
}
