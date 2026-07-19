"use client";

import { useState } from "react";

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
    <div className="mb-6 rounded border border-gray-800 p-4">
      <h2 className="mb-3 text-sm font-medium text-gray-500">Review a GitHub PR</h2>

      <div className="flex items-end gap-2">
        <div className="flex flex-col gap-1">
          <label className="text-xs text-gray-500" htmlFor="pr-number-input">
            PR number
          </label>
          <input
            id="pr-number-input"
            type="number"
            min={1}
            value={prNumberInput}
            onChange={(e) => setPrNumberInput(e.target.value)}
            className="w-24 rounded border border-gray-700 bg-gray-900 px-2 py-1 text-sm"
          />
        </div>
        <button
          onClick={handleStartReview}
          disabled={isReviewing || !prNumberInput}
          className="rounded bg-blue-900 px-4 py-2 text-sm text-white hover:bg-blue-800 disabled:opacity-50"
        >
          Review PR
        </button>
      </div>

      {confirmingPrNumber !== null && (
        <div className="mt-3 flex flex-col gap-2 rounded border border-yellow-900 bg-yellow-950/30 p-3">
          <p className="text-sm text-yellow-200">
            {reviewConfirmationMessage(confirmingPrNumber)}
          </p>
          <div className="flex gap-2">
            <button
              onClick={handleConfirmReview}
              disabled={isReviewing}
              className="rounded bg-green-900 px-4 py-2 text-sm text-white hover:bg-green-800 disabled:opacity-50"
            >
              {isReviewing ? "Reviewing..." : "Confirm review"}
            </button>
            <button
              onClick={() => setConfirmingPrNumber(null)}
              disabled={isReviewing}
              className="rounded border border-gray-700 px-4 py-2 text-sm text-gray-300 hover:bg-gray-800"
            >
              Cancel
            </button>
          </div>
        </div>
      )}

      {result && (
        <div className="mt-4 flex flex-col gap-1 text-sm">
          <span
            className={result.status === "failure" ? "text-red-400" : "text-green-400"}
          >
            commit status: {result.status}
          </span>
          <span className="text-gray-300">{describeStatus(result)}</span>
          <a
            href={result.pr_url}
            target="_blank"
            rel="noreferrer"
            className="text-blue-400 underline"
          >
            View PR #{result.pr_number}
          </a>
          {result.review_url && (
            <a
              href={result.review_url}
              target="_blank"
              rel="noreferrer"
              className="text-blue-400 underline"
            >
              View review
            </a>
          )}
        </div>
      )}

      {errorMessage && <p className="mt-3 text-sm text-red-400">{errorMessage}</p>}
    </div>
  );
}
