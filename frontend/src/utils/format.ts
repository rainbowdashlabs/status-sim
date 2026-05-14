const rtf = new Intl.RelativeTimeFormat('de', { numeric: 'auto' })

export function formatRelativeTime(timestamp: number): string {
  const diffSeconds = Math.max(0, Math.round(Date.now() / 1000 - timestamp))
  if (diffSeconds < 60) return rtf.format(-diffSeconds, 'second')
  if (diffSeconds < 3600) return rtf.format(-Math.round(diffSeconds / 60), 'minute')
  if (diffSeconds < 86400) return rtf.format(-Math.round(diffSeconds / 3600), 'hour')
  return rtf.format(-Math.round(diffSeconds / 86400), 'day')
}
