export function formatDate(value: string | null | undefined) {
  return value ? new Date(value).toLocaleDateString() : "—";
}

export function ageLabel(months: number) {
  return months < 24 ? `${months} months` : `${Math.floor(months / 12)} years`;
}
