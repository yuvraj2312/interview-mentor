import * as React from 'react'

import { cn } from '@/lib/utils'

interface ProgressProps extends React.HTMLAttributes<HTMLDivElement> {
  value: number
  max: number
}

const Progress = React.forwardRef<HTMLDivElement, ProgressProps>(({ value, max, className, ...props }, ref) => {
  const pct = max > 0 ? Math.min(100, Math.max(0, (value / max) * 100)) : 0
  return (
    <div ref={ref} className={cn('h-2 w-full overflow-hidden rounded-full bg-slate-200', className)} {...props}>
      <div className="h-full rounded-full bg-slate-900 transition-all" style={{ width: `${pct}%` }} />
    </div>
  )
})
Progress.displayName = 'Progress'

export { Progress }
