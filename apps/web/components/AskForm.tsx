"use client";

import { FormEvent, useState } from "react";

import { apiClient } from "@/lib/apiClient";
import { CitationChip, type Citation } from "@/components/CitationChip";

export function AskForm({
  orgId,
  repoId,
  filePathToId,
}: {
  orgId: string;
  repoId: string;
  filePathToId: Record<string, string>;
}) {
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState<string | null>(null);
  const [citations, setCitations] = useState<Citation[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    setIsSubmitting(true);

    const { data, error: apiError } = await apiClient.POST(
      "/api/organizations/{org_id}/repositories/{repo_id}/ask",
      {
        params: { path: { org_id: orgId, repo_id: repoId } },
        body: { question },
      },
    );

    setIsSubmitting(false);
    if (apiError || !data) {
      setError((apiError as { detail?: string })?.detail ?? "Failed to get an answer");
      return;
    }
    setAnswer(data.answer);
    setCitations(data.citations);
  }

  return (
    <div className="flex flex-col gap-4">
      <form className="flex gap-2" onSubmit={handleSubmit}>
        <input
          className="flex-1 rounded border border-gray-700 bg-gray-900 px-3 py-2"
          placeholder="Ask a question about this repository..."
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          required
        />
        <button
          type="submit"
          disabled={isSubmitting}
          className="rounded bg-blue-600 px-4 py-2 text-white hover:bg-blue-500 disabled:opacity-50"
        >
          {isSubmitting ? "Asking..." : "Ask"}
        </button>
      </form>

      {error && <p className="text-sm text-red-400">{error}</p>}

      {answer && (
        <div className="flex flex-col gap-3">
          <p className="text-gray-200">{answer}</p>
          {citations.length > 0 && (
            <div className="flex flex-col gap-2">
              <h3 className="text-sm font-medium text-gray-500">Citations</h3>
              {citations.map((citation) => (
                <CitationChip
                  key={`${citation.file_path}:${citation.start_line}`}
                  orgId={orgId}
                  repoId={repoId}
                  citation={citation}
                  fileId={filePathToId[citation.file_path]}
                />
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
