import { HelpCircle, Minus, TrendingDown, TrendingUp } from 'lucide-react'

import { Badge } from '@/components/ui/badge'
import type { SkillTrend } from '@/lib/api'

const TREND_CONFIG: Record<SkillTrend, { label: string; variant: 'good' | 'critical' | 'default'; Icon: typeof Minus }> = {
  improving: { label: 'Improving', variant: 'good', Icon: TrendingUp },
  declining: { label: 'Declining', variant: 'critical', Icon: TrendingDown },
  stable: { label: 'Stable', variant: 'default', Icon: Minus },
  insufficient_data: { label: 'Not enough data', variant: 'default', Icon: HelpCircle },
}

export function TrendBadge({ trend }: { trend: SkillTrend }) {
  const { label, variant, Icon } = TREND_CONFIG[trend]
  return (
    <Badge variant={variant}>
      <Icon className="size-3" />
      {label}
    </Badge>
  )
}
