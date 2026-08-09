"use client";

import { useParams, useRouter } from "next/navigation";
import { FormEvent, useState } from "react";

import { AuthShell } from "@/components/marketing/auth-shell";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { apiClient } from "@/lib/apiClient";

export default function ResetPasswordPage() {
  const { token } = useParams<{ token: string }>();
  const router = useRouter();
  const [newPassword, setNewPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    setIsSubmitting(true);

    const { error: apiError } = await apiClient.POST("/api/auth/reset-password", {
      body: { token, new_password: newPassword },
    });

    setIsSubmitting(false);
    if (apiError) {
      setError((apiError as { detail?: string }).detail ?? "This reset link is invalid or has expired");
      return;
    }
    router.push("/login");
  }

  return (
    <AuthShell>
      <Card className="border-border/60 p-6 shadow-sm md:p-8">
        <CardHeader className="px-0 pb-6">
          <CardTitle className="text-xl">Reset your password</CardTitle>
          <CardDescription>Choose a new password for your account.</CardDescription>
        </CardHeader>
        <CardContent className="px-0">
          <form className="flex flex-col gap-4" onSubmit={handleSubmit}>
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="newPassword">New password</Label>
              <Input
                id="newPassword"
                className="h-10"
                type="password"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                required
              />
            </div>
            {error && <p className="text-sm text-destructive">{error}</p>}
            <Button type="submit" disabled={isSubmitting} className="mt-1 h-10">
              {isSubmitting ? "Resetting..." : "Reset password"}
            </Button>
          </form>
        </CardContent>
      </Card>
    </AuthShell>
  );
}
