"use client";

import { FormEvent, useState } from "react";

import { CitationChip, type Citation } from "@/components/CitationChip";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { apiClient } from "@/lib/apiClient";

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
        <Input
          className="h-10 flex-1"
          placeholder="Ask a question about this repository..."
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          required
        />
        <Button type="submit" className="h-10" disabled={isSubmitting}>
          {isSubmitting ? "Asking..." : "Ask"}
        </Button>
      </form>

      {error && (
        <p className="text-sm text-destructive" role="alert">
          {error}
        </p>
      )}

      {answer && (
        <div className="flex flex-col gap-3">
          <p className="text-sm text-foreground/90">{answer}</p>
          {citations.length > 0 && (
            <div className="flex flex-col gap-2">
              <h3 className="text-sm font-medium text-muted-foreground">Citations</h3>
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
