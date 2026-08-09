"use client";

import { FormEvent, useState } from "react";

import { AuthShell } from "@/components/marketing/auth-shell";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { apiClient } from "@/lib/apiClient";

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setIsSubmitting(true);

    await apiClient.POST("/api/auth/request-password-reset", { body: { email } });

    setIsSubmitting(false);
    setSubmitted(true);
  }

  if (submitted) {
    return (
      <AuthShell>
        <Card className="border-border/60 p-6 text-center shadow-sm md:p-8">
          <CardHeader className="px-0">
            <CardTitle className="text-xl">Check your email</CardTitle>
            <CardDescription>
              If an account exists for {email}, we&apos;ve sent a password reset link.
            </CardDescription>
          </CardHeader>
        </Card>
      </AuthShell>
    );
  }

  return (
    <AuthShell>
      <Card className="border-border/60 p-6 shadow-sm md:p-8">
        <CardHeader className="px-0 pb-6">
          <CardTitle className="text-xl">Forgot your password?</CardTitle>
          <CardDescription>We&apos;ll email you a link to reset it.</CardDescription>
        </CardHeader>
        <CardContent className="px-0">
          <form className="flex flex-col gap-4" onSubmit={handleSubmit}>
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="email">Email</Label>
              <Input
                id="email"
                className="h-10"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
            </div>
            <Button type="submit" disabled={isSubmitting} className="mt-1 h-10">
              {isSubmitting ? "Sending..." : "Send reset link"}
            </Button>
          </form>
        </CardContent>
      </Card>
    </AuthShell>
  );
}
