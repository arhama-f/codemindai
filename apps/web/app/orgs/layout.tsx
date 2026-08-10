import { AppHeader } from "@/components/app/app-header";

export default function OrgsLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen">
      <AppHeader />
      {children}
    </div>
  );
}
