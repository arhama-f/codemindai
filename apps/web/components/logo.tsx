interface LogoProps {
  size?: number;
  className?: string;
}

export function Logo({ size = 28, className }: LogoProps) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 32 32"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={className}
      aria-hidden="true"
    >
      <rect width="32" height="32" rx="8" fill="hsl(var(--primary))" />
      <line x1="10" y1="21" x2="16" y2="11" stroke="hsl(var(--primary-foreground))" strokeOpacity="0.55" strokeWidth="1.4" />
      <line x1="16" y1="11" x2="22" y2="21" stroke="hsl(var(--primary-foreground))" strokeOpacity="0.55" strokeWidth="1.4" />
      <line x1="10" y1="21" x2="22" y2="21" stroke="hsl(var(--primary-foreground))" strokeOpacity="0.35" strokeWidth="1.4" />
      <circle cx="16" cy="11" r="2.6" fill="hsl(var(--primary-foreground))" />
      <circle cx="10" cy="21" r="2.2" fill="hsl(var(--primary-foreground))" fillOpacity="0.85" />
      <circle cx="22" cy="21" r="2.2" fill="hsl(var(--primary-foreground))" fillOpacity="0.85" />
    </svg>
  );
}
