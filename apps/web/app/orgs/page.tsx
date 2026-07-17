"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";

import { apiClient } from "@/lib/apiClient";

export default function OrgsPage() {
  const { data, isLoading, isError } = useQuery({
    queryKey: ["organizations"],
    queryFn: async () => {
      const { data, error } = await apiClient.GET("/api/organizations");
      if (error) throw error;
      return data;
    },
  });

  if (isLoading) return <main className="p-6 text-gray-400">Loading...</main>;
  if (isError) {
    return (
      <main className="p-6 text-gray-400">
        Failed to load organizations.{" "}
        <Link href="/login" className="underline">
          Sign in
        </Link>
      </main>
    );
  }

  return (
    <main className="mx-auto max-w-2xl px-6 py-16">
      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Organizations</h1>
        <Link
          href="/orgs/new"
          className="rounded bg-blue-600 px-3 py-1.5 text-white hover:bg-blue-500"
        >
          New organization
        </Link>
      </div>
      <ul className="flex flex-col gap-2">
        {data?.map((org) => (
          <li key={org.id}>
            <Link
              href={`/orgs/${org.id}`}
              className="block rounded border border-gray-800 px-4 py-3 hover:bg-gray-900"
            >
              <span className="font-medium">{org.name}</span>{" "}
              <span className="text-sm text-gray-500">({org.role})</span>
            </Link>
          </li>
        ))}
        {data?.length === 0 && <p className="text-gray-500">No organizations yet.</p>}
      </ul>
    </main>
  );
}
