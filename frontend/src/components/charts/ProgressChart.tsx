import { CartesianGrid, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'

import { ChartLegend } from '@/components/charts/ChartLegend'
import { ChartTooltip } from '@/components/charts/ChartTooltip'
import { CHART_AXIS_COLOR, CHART_GRID_COLOR, SERIES_COLORS } from '@/lib/chartPalette'
import type { InterviewSessionListItem } from '@/lib/api'

interface ProgressChartProps {
  sessions: InterviewSessionListItem[]
}

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString(undefined, { month: 'short', day: 'numeric' })
}

export function ProgressChart({ sessions }: ProgressChartProps) {
  const data = sessions
    .filter((s) => s.status === 'complete' && s.completed_at && s.avg_technical_score !== null)
    .sort((a, b) => new Date(a.completed_at!).getTime() - new Date(b.completed_at!).getTime())
    .map((s) => ({
      date: formatDate(s.completed_at!),
      Technical: s.avg_technical_score,
      Communication: s.avg_communication_score,
      Completeness: s.avg_completeness_score,
    }))

  return (
    <ResponsiveContainer width="100%" height={280}>
      <LineChart data={data} margin={{ top: 8, right: 24, bottom: 8, left: 8 }}>
        <CartesianGrid vertical={false} stroke={CHART_GRID_COLOR} />
        <XAxis
          dataKey="date"
          stroke={CHART_AXIS_COLOR}
          tick={{ fontSize: 12, fill: '#64748b' }}
          axisLine={{ stroke: CHART_AXIS_COLOR }}
          tickLine={false}
        />
        <YAxis
          domain={[0, 10]}
          stroke={CHART_AXIS_COLOR}
          tick={{ fontSize: 12, fill: '#64748b' }}
          axisLine={{ stroke: CHART_AXIS_COLOR }}
          tickLine={false}
        />
        <Tooltip content={<ChartTooltip />} />
        <Legend content={<ChartLegend />} verticalAlign="top" align="left" height={32} />
        <Line
          type="monotone"
          dataKey="Technical"
          stroke={SERIES_COLORS.technical}
          strokeWidth={2}
          dot={{ r: 4, fill: SERIES_COLORS.technical, stroke: '#ffffff', strokeWidth: 2 }}
        />
        <Line
          type="monotone"
          dataKey="Communication"
          stroke={SERIES_COLORS.communication}
          strokeWidth={2}
          dot={{ r: 4, fill: SERIES_COLORS.communication, stroke: '#ffffff', strokeWidth: 2 }}
        />
        <Line
          type="monotone"
          dataKey="Completeness"
          stroke={SERIES_COLORS.completeness}
          strokeWidth={2}
          dot={{ r: 4, fill: SERIES_COLORS.completeness, stroke: '#ffffff', strokeWidth: 2 }}
        />
      </LineChart>
    </ResponsiveContainer>
  )
}
