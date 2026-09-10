import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { GraduationCap } from 'lucide-react'
import { Link, useNavigate } from 'react-router-dom'

import { login, ApiError } from '@/lib/api'
import { useAuthStore } from '@/store/authStore'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'

export function LoginPage() {
  const navigate = useNavigate()
  const setTokens = useAuthStore((state) => state.setTokens)
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')

  const mutation = useMutation({
    mutationFn: () => login(email, password),
    onSuccess: (tokens) => {
      setTokens({ accessToken: tokens.access_token, refreshToken: tokens.refresh_token })
      navigate('/dashboard', { replace: true })
    },
  })

  return (
    <div className="flex min-h-svh items-center justify-center bg-surface-muted px-4">
      <div className="w-full max-w-sm">
        <div className="mb-6 flex justify-center">
          <span className="flex size-11 items-center justify-center rounded-lg bg-ink-900 text-white shadow-sm">
            <GraduationCap className="size-6" />
          </span>
        </div>
        <Card>
          <CardHeader>
            <CardTitle>Log in</CardTitle>
            <CardDescription>Welcome back to Interview Mentor.</CardDescription>
          </CardHeader>
          <CardContent>
            <form
              className="flex flex-col gap-4"
              onSubmit={(event) => {
                event.preventDefault()
                mutation.mutate()
              }}
            >
              <div className="flex flex-col gap-2">
                <Label htmlFor="email">Email</Label>
                <Input
                  id="email"
                  type="email"
                  autoComplete="email"
                  required
                  value={email}
                  onChange={(event) => setEmail(event.target.value)}
                />
              </div>
              <div className="flex flex-col gap-2">
                <Label htmlFor="password">Password</Label>
                <Input
                  id="password"
                  type="password"
                  autoComplete="current-password"
                  required
                  value={password}
                  onChange={(event) => setPassword(event.target.value)}
                />
              </div>
              {mutation.isError && (
                <p className="text-sm text-danger-600">
                  {mutation.error instanceof ApiError ? mutation.error.message : 'Login failed'}
                </p>
              )}
              <Button type="submit" disabled={mutation.isPending}>
                {mutation.isPending ? 'Logging in…' : 'Log in'}
              </Button>
            </form>
            <p className="mt-4 text-center text-sm text-ink-400">
              Don't have an account?{' '}
              <Link to="/signup" className="font-medium text-ink-900 underline">
                Sign up
              </Link>
            </p>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
