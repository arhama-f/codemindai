"use client";

import { useEffect, useState } from "react";

import { API_URL } from "@/lib/apiClient";

interface JobEvent {
  status: string;
  progress_percent: number;
  message: string | null;
}

const TERMINAL_STATUSES = new Set(["completed", "failed"]);

export function JobProgressBar({
  orgId,
  jobId,
  onStatusChange,
}: {
  orgId: string;
  jobId: string;
  onStatusChange?: (status: string) => void;
}) {
  const [job, setJob] = useState<JobEvent | null>(null);

  useEffect(() => {
    const source = new EventSource(`${API_URL}/api/organizations/${orgId}/jobs/${jobId}/events`, {
      withCredentials: true,
    });

    source.onmessage = (event) => {
      const payload: JobEvent = JSON.parse(event.data);
      setJob(payload);
      onStatusChange?.(payload.status);
      if (TERMINAL_STATUSES.has(payload.status)) {
        source.close();
      }
    };
    source.onerror = () => source.close();

    return () => source.close();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [orgId, jobId]);

  if (!job) {
    return <p className="text-sm text-gray-500">Connecting...</p>;
  }

  return (
    <div className="flex flex-col gap-1">
      <div className="h-2 w-full overflow-hidden rounded bg-gray-800">
        <div
          className="h-full bg-blue-600 transition-all"
          style={{ width: `${job.progress_percent}%` }}
        />
      </div>
      <p className="text-sm text-gray-400">
        {job.status}
        {job.message ? ` — ${job.message}` : ""} ({job.progress_percent}%)
      </p>
    </div>
  );
}
