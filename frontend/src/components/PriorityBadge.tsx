import { Badge } from '@/components/ui/badge'
import type { RoadmapPriority } from '@/lib/api'

const PRIORITY_CONFIG: Record<RoadmapPriority, { label: string; variant: 'good' | 'warning' | 'critical' }> = {
  high: { label: 'High priority', variant: 'critical' },
  medium: { label: 'Medium priority', variant: 'warning' },
  low: { label: 'Low priority', variant: 'good' },
}

export function PriorityBadge({ priority }: { priority: RoadmapPriority }) {
  const { label, variant } = PRIORITY_CONFIG[priority]
  return <Badge variant={variant}>{label}</Badge>
}
