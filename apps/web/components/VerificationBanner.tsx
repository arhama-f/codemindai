"use client";

import { useQuery } from "@tanstack/react-query";
import { useState } from "react";

import { apiClient } from "@/lib/apiClient";

export function VerificationBanner() {
  const [resent, setResent] = useState(false);
  const meQuery = useQuery({
    queryKey: ["me"],
    queryFn: async () => {
      const { data, error } = await apiClient.GET("/api/auth/me");
      if (error) throw error;
      return data;
    },
  });

  if (!meQuery.data || meQuery.data.is_verified) return null;

  async function resendVerification() {
    await apiClient.POST("/api/auth/resend-verification");
    setResent(true);
  }

  return (
    <div className="mb-6 flex items-center justify-between rounded border border-yellow-800 bg-yellow-950/40 px-4 py-3 text-sm text-yellow-300">
      <span>Please verify your email address.</span>
      <button
        onClick={resendVerification}
        disabled={resent}
        className="rounded border border-yellow-700 px-3 py-1 hover:bg-yellow-900 disabled:opacity-50"
      >
        {resent ? "Verification email sent" : "Resend verification email"}
      </button>
    </div>
  );
}
