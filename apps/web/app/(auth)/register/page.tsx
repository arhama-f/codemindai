"use client";

import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";

import { AuthShell } from "@/components/marketing/auth-shell";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Separator } from "@/components/ui/separator";
import { API_URL, apiClient } from "@/lib/apiClient";

export default function RegisterPage() {
  const router = useRouter();
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    setIsSubmitting(true);

    const { error: apiError } = await apiClient.POST("/api/auth/register", {
      body: { email, password, full_name: fullName },
    });

    setIsSubmitting(false);
    if (apiError) {
      setError((apiError as { detail?: string }).detail ?? "Registration failed");
      return;
    }
    router.push("/orgs");
  }

  return (
    <AuthShell>
      <Card className="border-border/60 p-6 shadow-sm md:p-8">
        <CardHeader className="px-0 pb-6">
          <CardTitle className="text-xl">Create your account</CardTitle>
          <CardDescription>Start indexing your first repository for free.</CardDescription>
        </CardHeader>
        <CardContent className="px-0">
          <form className="flex flex-col gap-4" onSubmit={handleSubmit}>
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="fullName">Full name</Label>
              <Input
                id="fullName"
                className="h-10"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                required
              />
            </div>
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
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="password">Password</Label>
              <Input
                id="password"
                className="h-10"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
            </div>
            {error && <p className="text-sm text-destructive">{error}</p>}
            <Button type="submit" disabled={isSubmitting} className="mt-1 h-10">
              {isSubmitting ? "Creating account..." : "Create account"}
            </Button>
          </form>

          <div className="my-6 flex items-center gap-3">
            <Separator className="flex-1" />
            <span className="text-xs text-muted-foreground">or continue with</span>
            <Separator className="flex-1" />
          </div>

          <div className="flex flex-col gap-2">
            <Button
              variant="outline"
              className="h-10"
              nativeButton={false}
              render={<a href={`${API_URL}/api/auth/oauth/google/start`} />}
            >
              Sign up with Google
            </Button>
            <Button
              variant="outline"
              className="h-10"
              nativeButton={false}
              render={<a href={`${API_URL}/api/auth/oauth/github/start`} />}
            >
              Sign up with GitHub
            </Button>
          </div>
        </CardContent>
        <CardFooter className="justify-center bg-transparent px-0 pt-6 text-sm text-muted-foreground">
          Already have an account?{" "}
          <a href="/login" className="ml-1 text-primary hover:underline">
            Sign in
          </a>
        </CardFooter>
      </Card>
    </AuthShell>
  );
}
