"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { useParams } from "next/navigation";

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
    <main className="mx-auto flex max-w-sm flex-col gap-4 px-6 py-24 text-center">
      {verifyQuery.isLoading && <p className="text-gray-400">Verifying your email...</p>}
      {verifyQuery.isSuccess && (
        <>
          <h1 className="text-2xl font-semibold">Email verified</h1>
          <p className="text-gray-400">Your email address has been verified.</p>
        </>
      )}
      {verifyQuery.isError && (
        <>
          <h1 className="text-2xl font-semibold">Verification failed</h1>
          <p className="text-gray-400">
            This verification link is invalid or has expired.
          </p>
        </>
      )}
      <Link href="/orgs" className="text-blue-400 hover:text-blue-300">
        Go to your organizations
      </Link>
    </main>
  );
}
