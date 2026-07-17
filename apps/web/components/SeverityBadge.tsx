const SEVERITY_STYLES: Record<string, string> = {
  critical: "bg-red-950 text-red-300 border-red-800",
  high: "bg-orange-950 text-orange-300 border-orange-800",
  medium: "bg-yellow-950 text-yellow-300 border-yellow-800",
  low: "bg-gray-800 text-gray-300 border-gray-700",
};

export function SeverityBadge({ severity }: { severity: string }) {
  const style = SEVERITY_STYLES[severity] ?? SEVERITY_STYLES.low;
  return (
    <span className={`rounded border px-2 py-0.5 text-xs font-medium ${style}`}>
      {severity}
    </span>
  );
}
