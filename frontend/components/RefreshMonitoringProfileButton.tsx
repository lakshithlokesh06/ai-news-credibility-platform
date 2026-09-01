"use client";

import { RefreshCw } from "lucide-react";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { apiBaseUrl, apiErrorMessage } from "@/lib/api";

type RefreshMonitoringProfileButtonProps = {
  trainingRunId: string;
};

export function RefreshMonitoringProfileButton({ trainingRunId }: RefreshMonitoringProfileButtonProps) {
  const router = useRouter();
  const [status, setStatus] = useState<"idle" | "saving" | "saved" | "failed">("idle");
  const [message, setMessage] = useState<string | null>(null);

  async function refreshProfile() {
    setStatus("saving");
    setMessage(null);
    try {
      const response = await fetch(
        `${apiBaseUrl}/api/v1/monitoring/models/${trainingRunId}/reference-profile`,
        { method: "POST" },
      );
      const payload = await response.json();
      if (!response.ok) {
        setMessage(apiErrorMessage(payload, "Profile refresh failed."));
        setStatus("failed");
        return;
      }
      setStatus("saved");
      router.refresh();
    } catch {
      setMessage("Profile refresh failed. Check backend availability and model artifacts.");
      setStatus("failed");
    }
  }

  return (
    <div className="grid gap-2">
      <button
        type="button"
        onClick={refreshProfile}
        disabled={status === "saving"}
        className="inline-flex items-center justify-center gap-2 rounded-md bg-ink px-4 py-2 text-sm font-semibold text-white disabled:cursor-not-allowed disabled:opacity-60"
      >
        <RefreshCw aria-hidden="true" className={`h-4 w-4 ${status === "saving" ? "animate-spin" : ""}`} />
        {status === "saving" ? "Refreshing" : "Refresh profile"}
      </button>
      {status === "saved" ? <p className="text-xs text-emerald-700">Reference profile refreshed.</p> : null}
      {status === "failed" ? (
        <p className="text-xs text-rose-700">{message}</p>
      ) : null}
    </div>
  );
}
