//Convert ISO string to readable date/time.
export function formatDateTime(isoString: string): string {
  const date = new Date(isoString);
  return date.toLocaleString(undefined, {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}


// Calculate delay in minutes between two timestamps.
export function calculateDelayMinutes(planned: string, actual: string): number {
  const diffMs = new Date(actual).getTime() - new Date(planned).getTime();
  return Math.round(diffMs / 60000);
}
