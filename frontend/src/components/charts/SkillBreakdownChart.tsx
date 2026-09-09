import { Bar, BarChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'

import { ChartLegend } from '@/components/charts/ChartLegend'
import { ChartTooltip } from '@/components/charts/ChartTooltip'
import { CHART_AXIS_COLOR, CHART_GRID_COLOR, SERIES_COLORS } from '@/lib/chartPalette'
import type { SkillProfileTopicStatOut } from '@/lib/api'

interface SkillBreakdownChartProps {
  topics: SkillProfileTopicStatOut[]
}

export function SkillBreakdownChart({ topics }: SkillBreakdownChartProps) {
  const data = topics.map((t) => ({
    topic: t.topic,
    Technical: t.avg_technical_score,
    Communication: t.avg_communication_score,
    Completeness: t.avg_completeness_score,
  }))

  const height = Math.max(160, data.length * 56)

  return (
    <ResponsiveContainer width="100%" height={height}>
      <BarChart data={data} layout="vertical" margin={{ top: 8, right: 24, bottom: 8, left: 8 }}>
        <CartesianGrid horizontal={false} stroke={CHART_GRID_COLOR} />
        <XAxis
          type="number"
          domain={[0, 10]}
          stroke={CHART_AXIS_COLOR}
          tick={{ fontSize: 12, fill: '#64748b' }}
          axisLine={{ stroke: CHART_AXIS_COLOR }}
          tickLine={false}
        />
        <YAxis
          type="category"
          dataKey="topic"
          width={140}
          stroke={CHART_AXIS_COLOR}
          tick={{ fontSize: 12, fill: '#334155' }}
          axisLine={{ stroke: CHART_AXIS_COLOR }}
          tickLine={false}
        />
        <Tooltip content={<ChartTooltip />} cursor={{ fill: '#f1f5f9' }} />
        <Legend content={<ChartLegend />} verticalAlign="top" align="left" height={32} />
        <Bar dataKey="Technical" fill={SERIES_COLORS.technical} radius={[0, 4, 4, 0]} barSize={12} />
        <Bar dataKey="Communication" fill={SERIES_COLORS.communication} radius={[0, 4, 4, 0]} barSize={12} />
        <Bar dataKey="Completeness" fill={SERIES_COLORS.completeness} radius={[0, 4, 4, 0]} barSize={12} />
      </BarChart>
    </ResponsiveContainer>
  )
}
