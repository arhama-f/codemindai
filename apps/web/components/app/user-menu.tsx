"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";

import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { apiClient } from "@/lib/apiClient";

export function UserMenu() {
  const router = useRouter();
  const { orgId } = useParams<{ orgId?: string }>();

  const meQuery = useQuery({
    queryKey: ["me"],
    queryFn: async () => {
      const { data, error } = await apiClient.GET("/api/auth/me");
      if (error) throw error;
      return data;
    },
  });

  async function handleSignOut() {
    await apiClient.POST("/api/auth/logout");
    router.push("/login");
  }

  const name = meQuery.data?.full_name || meQuery.data?.email || "";
  const initial = name.charAt(0).toUpperCase() || "?";

  return (
    <DropdownMenu>
      <DropdownMenuTrigger
        render={
          <Button
            variant="ghost"
            size="icon"
            className="size-8 rounded-full bg-secondary text-sm font-medium"
          />
        }
      >
        {initial}
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-56">
        <div className="px-1.5 py-1">
          <p className="truncate text-sm font-medium text-foreground">{meQuery.data?.full_name}</p>
          <p className="truncate text-xs text-muted-foreground">{meQuery.data?.email}</p>
        </div>
        <DropdownMenuSeparator />
        {orgId && (
          <DropdownMenuItem render={<Link href={`/orgs/${orgId}/billing`} />}>Billing</DropdownMenuItem>
        )}
        <DropdownMenuItem variant="destructive" onClick={handleSignOut}>
          Sign out
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
