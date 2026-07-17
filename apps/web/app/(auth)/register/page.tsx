"use client";

import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";

import { apiClient } from "@/lib/apiClient";

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
    <main className="mx-auto flex max-w-sm flex-col gap-4 px-6 py-24">
      <h1 className="text-2xl font-semibold">Create your account</h1>
      <form className="flex flex-col gap-3" onSubmit={handleSubmit}>
        <input
          className="rounded border border-gray-700 bg-gray-900 px-3 py-2"
          placeholder="Full name"
          value={fullName}
          onChange={(e) => setFullName(e.target.value)}
          required
        />
        <input
          className="rounded border border-gray-700 bg-gray-900 px-3 py-2"
          placeholder="Email"
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
        />
        <input
          className="rounded border border-gray-700 bg-gray-900 px-3 py-2"
          placeholder="Password"
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
        />
        {error && <p className="text-sm text-red-400">{error}</p>}
        <button
          type="submit"
          disabled={isSubmitting}
          className="rounded bg-blue-600 px-4 py-2 text-white hover:bg-blue-500 disabled:opacity-50"
        >
          {isSubmitting ? "Creating account..." : "Create account"}
        </button>
      </form>
    </main>
  );
}
