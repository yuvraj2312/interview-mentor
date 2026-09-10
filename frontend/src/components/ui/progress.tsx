import * as React from 'react'

import { cn } from '@/lib/utils'

interface ProgressProps extends React.HTMLAttributes<HTMLDivElement> {
  value: number
  max: number
  indicatorClassName?: string
}

const Progress = React.forwardRef<HTMLDivElement, ProgressProps>(
  ({ value, max, className, indicatorClassName, ...props }, ref) => {
    const pct = max > 0 ? Math.min(100, Math.max(0, (value / max) * 100)) : 0
    return (
      <div ref={ref} className={cn('h-2 w-full overflow-hidden rounded-full bg-ink-100', className)} {...props}>
        <div
          className={cn('h-full rounded-full bg-ink-900 transition-all', indicatorClassName)}
          style={{ width: `${pct}%` }}
        />
      </div>
    )
  },
)
Progress.displayName = 'Progress'

export { Progress }
