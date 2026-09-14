export function SparseDataBanner({ message }: { message: string }) {
  return (
    <div className="rounded-md bg-warning-50 px-4 py-3 text-sm text-warning-700">
      {message}
    </div>
  )
}
