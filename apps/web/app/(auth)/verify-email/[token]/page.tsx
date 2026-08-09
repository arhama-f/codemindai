"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { useParams } from "next/navigation";

import { AuthShell } from "@/components/marketing/auth-shell";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { apiClient } from "@/lib/apiClient";

export default function VerifyEmailPage() {
  const { token } = useParams<{ token: string }>();

  const verifyQuery = useQuery({
    queryKey: ["verify-email", token],
    queryFn: async () => {
      const { data, error } = await apiClient.GET("/api/auth/verify-email/{token}", {
        params: { path: { token } },
      });
      if (error) throw error;
      return data;
    },
    retry: false,
  });

  return (
    <AuthShell>
      <Card className="border-border/60 p-6 text-center shadow-sm md:p-8">
        <CardHeader className="items-center px-0">
          {verifyQuery.isLoading && (
            <CardDescription>Verifying your email...</CardDescription>
          )}
          {verifyQuery.isSuccess && (
            <>
              <CardTitle className="text-xl">Email verified</CardTitle>
              <CardDescription>Your email address has been verified.</CardDescription>
            </>
          )}
          {verifyQuery.isError && (
            <>
              <CardTitle className="text-xl">Verification failed</CardTitle>
              <CardDescription>This verification link is invalid or has expired.</CardDescription>
            </>
          )}
        </CardHeader>
        <CardContent className="px-0 pt-4">
          <Button
            variant="outline"
            className="h-10 w-full"
            nativeButton={false}
            render={<Link href="/orgs" />}
          >
            Go to your organizations
          </Button>
        </CardContent>
      </Card>
    </AuthShell>
  );
}
