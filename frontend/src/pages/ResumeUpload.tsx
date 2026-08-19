import { useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { useUploadResume } from '@/hooks/useResume'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'

export function ResumeUploadPage() {
  const navigate = useNavigate()
  const [file, setFile] = useState<File | null>(null)
  const upload = useUploadResume()

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault()
    if (!file) return
    const resume = await upload.mutateAsync(file)
    navigate(`/resumes/${resume.id}/review`)
  }

  return (
    <div className="min-h-svh bg-slate-50">
      <main className="mx-auto max-w-xl px-6 py-16">
        <Card>
          <CardHeader>
            <CardTitle>Upload your resume</CardTitle>
            <CardDescription>PDF or DOCX. We'll extract your skills, experience, and education.</CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="flex flex-col gap-4">
              <input
                type="file"
                accept=".pdf,.docx"
                onChange={(event) => setFile(event.target.files?.[0] ?? null)}
                className="text-sm"
              />
              {upload.isError && <p className="text-sm text-red-600">Upload failed. Please try again.</p>}
              <Button type="submit" disabled={!file || upload.isPending}>
                {upload.isPending ? 'Uploading...' : 'Upload'}
              </Button>
            </form>
          </CardContent>
        </Card>
      </main>
    </div>
  )
}
