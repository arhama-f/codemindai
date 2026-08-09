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

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    setIsSubmitting(true);

    const { error: apiError } = await apiClient.POST("/api/auth/login", {
      body: { email, password },
    });

    setIsSubmitting(false);
    if (apiError) {
      setError((apiError as { detail?: string }).detail ?? "Login failed");
      return;
    }
    router.push("/orgs");
  }

  return (
    <AuthShell>
      <Card className="border-border/60 p-6 shadow-sm md:p-8">
        <CardHeader className="px-0 pb-6">
          <CardTitle className="text-xl">Sign in</CardTitle>
          <CardDescription>Welcome back — enter your details to continue.</CardDescription>
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
            <div className="flex flex-col gap-1.5">
              <div className="flex items-center justify-between">
                <Label htmlFor="password">Password</Label>
                <a href="/forgot-password" className="text-xs text-muted-foreground hover:text-foreground">
                  Forgot password?
                </a>
              </div>
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
              {isSubmitting ? "Signing in..." : "Sign in"}
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
              Sign in with Google
            </Button>
            <Button
              variant="outline"
              className="h-10"
              nativeButton={false}
              render={<a href={`${API_URL}/api/auth/oauth/github/start`} />}
            >
              Sign in with GitHub
            </Button>
          </div>
        </CardContent>
        <CardFooter className="justify-center bg-transparent px-0 pt-6 text-sm text-muted-foreground">
          Don&apos;t have an account?{" "}
          <a href="/register" className="ml-1 text-primary hover:underline">
            Sign up
          </a>
        </CardFooter>
      </Card>
    </AuthShell>
  );
}
