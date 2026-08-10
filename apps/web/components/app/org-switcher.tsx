"use client";

import { useQuery } from "@tanstack/react-query";
import { ChevronsUpDown, Plus } from "lucide-react";
import Link from "next/link";
import { useParams } from "next/navigation";

import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { apiClient } from "@/lib/apiClient";

export function OrgSwitcher() {
  const { orgId } = useParams<{ orgId?: string }>();

  const orgsQuery = useQuery({
    queryKey: ["organizations"],
    queryFn: async () => {
      const { data, error } = await apiClient.GET("/api/organizations");
      if (error) throw error;
      return data;
    },
  });

  const currentOrg = orgsQuery.data?.find((org) => org.id === orgId);

  return (
    <DropdownMenu>
      <DropdownMenuTrigger
        render={<Button variant="ghost" className="h-8 max-w-48 gap-1.5 px-2 text-sm font-medium" />}
      >
        <span className="truncate">{currentOrg?.name ?? "Organizations"}</span>
        <ChevronsUpDown className="size-3.5 shrink-0 text-muted-foreground" />
      </DropdownMenuTrigger>
      <DropdownMenuContent align="start" className="w-56">
        {orgsQuery.data?.map((org) => (
          <DropdownMenuItem key={org.id} render={<Link href={`/orgs/${org.id}`} />}>
            <span className="truncate">{org.name}</span>
          </DropdownMenuItem>
        ))}
        {!!orgsQuery.data?.length && <DropdownMenuSeparator />}
        <DropdownMenuItem render={<Link href="/orgs" />}>All organizations</DropdownMenuItem>
        <DropdownMenuItem render={<Link href="/orgs/new" />}>
          <Plus className="size-4" />
          New organization
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
