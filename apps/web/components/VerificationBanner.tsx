"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";

import { Button } from "@/components/ui/button";
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
    <div className="mb-6 flex items-center justify-between rounded-lg border border-amber-500/20 bg-amber-500/10 px-4 py-3 text-sm text-amber-400">
      <span>Please verify your email address.</span>
      <Button size="sm" variant="outline" onClick={resendVerification} disabled={resent}>
        {resent ? "Verification email sent" : "Resend verification email"}
      </Button>
    </div>
  );
}
