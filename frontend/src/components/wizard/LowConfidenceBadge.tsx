export function LowConfidenceBadge({ field, flagged }: { field: string; flagged: string[] }) {
  const isFlagged = flagged.some((f) => f.startsWith(field))
  if (!isFlagged) return null
  return (
    <span className="ml-2 rounded-full bg-warning-50 px-2 py-0.5 text-xs font-medium text-warning-700">
      Please review
    </span>
  )
}
