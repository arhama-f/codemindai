"use client";

import { useState } from "react";

import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { apiClient } from "@/lib/apiClient";
import { extractErrorDetail } from "@/lib/proposedChanges";
import { describeStatus, reviewConfirmationMessage, type PRReview } from "@/lib/prReviews";

export function PRReviewPanel({ orgId }: { orgId: string }) {
  const [prNumberInput, setPrNumberInput] = useState("");
  const [confirmingPrNumber, setConfirmingPrNumber] = useState<number | null>(null);
  const [isReviewing, setIsReviewing] = useState(false);
  const [result, setResult] = useState<PRReview | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  function handleStartReview() {
    const prNumber = Number(prNumberInput);
    if (!Number.isInteger(prNumber) || prNumber <= 0) {
      setErrorMessage("Enter a valid PR number.");
      return;
    }
    setErrorMessage(null);
    setResult(null);
    setConfirmingPrNumber(prNumber);
  }

  async function handleConfirmReview() {
    if (confirmingPrNumber === null) return;
    setIsReviewing(true);
    setErrorMessage(null);

    const { data, error } = await apiClient.POST("/api/organizations/{org_id}/pr-reviews", {
      params: { path: { org_id: orgId } },
      body: { pr_number: confirmingPrNumber },
    });

    setIsReviewing(false);
    setConfirmingPrNumber(null);
    if (error) {
      setErrorMessage(extractErrorDetail(error) ?? "Failed to review PR.");
      return;
    }
    setResult(data);
  }

  return (
    <Card className="mb-6 gap-3 p-4 shadow-none">
      <CardHeader className="p-0">
        <CardTitle className="text-sm font-medium text-muted-foreground">
          Review a GitHub PR
        </CardTitle>
      </CardHeader>
      <CardContent className="p-0">
        <div className="flex items-end gap-2">
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="pr-number-input" className="text-xs text-muted-foreground">
              PR number
            </Label>
            <Input
              id="pr-number-input"
              type="number"
              min={1}
              value={prNumberInput}
              onChange={(e) => setPrNumberInput(e.target.value)}
              className="h-8 w-24"
            />
          </div>
          <Button
            size="sm"
            variant="secondary"
            onClick={handleStartReview}
            disabled={isReviewing || !prNumberInput}
          >
            Review PR
          </Button>
        </div>

        <AlertDialog
          open={confirmingPrNumber !== null}
          onOpenChange={(open) => !open && setConfirmingPrNumber(null)}
        >
          <AlertDialogContent>
            <AlertDialogHeader>
              <AlertDialogTitle>Review PR #{confirmingPrNumber}?</AlertDialogTitle>
              <AlertDialogDescription>
                {confirmingPrNumber !== null && reviewConfirmationMessage(confirmingPrNumber)}
              </AlertDialogDescription>
            </AlertDialogHeader>
            <AlertDialogFooter>
              <AlertDialogCancel disabled={isReviewing}>Cancel</AlertDialogCancel>
              <AlertDialogAction onClick={handleConfirmReview} disabled={isReviewing}>
                {isReviewing ? "Reviewing..." : "Confirm review"}
              </AlertDialogAction>
            </AlertDialogFooter>
          </AlertDialogContent>
        </AlertDialog>

        {result && (
          <div className="mt-4 flex flex-col gap-1 text-sm">
            <span className={result.status === "failure" ? "text-destructive" : "text-emerald-400"}>
              commit status: {result.status}
            </span>
            <span className="text-foreground/90">{describeStatus(result)}</span>
            <a
              href={result.pr_url}
              target="_blank"
              rel="noreferrer"
              className="text-primary hover:underline"
            >
              View PR #{result.pr_number}
            </a>
            {result.review_url && (
              <a
                href={result.review_url}
                target="_blank"
                rel="noreferrer"
                className="text-primary hover:underline"
              >
                View review
              </a>
            )}
          </div>
        )}

        {errorMessage && (
          <p className="mt-3 text-sm text-destructive" role="alert">
            {errorMessage}
          </p>
        )}
      </CardContent>
    </Card>
  );
}
