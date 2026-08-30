"use client";

import { RefreshCw } from "lucide-react";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { apiBaseUrl } from "@/lib/api";

type RefreshMonitoringProfileButtonProps = {
  trainingRunId: string;
};

export function RefreshMonitoringProfileButton({ trainingRunId }: RefreshMonitoringProfileButtonProps) {
  const router = useRouter();
  const [status, setStatus] = useState<"idle" | "saving" | "saved" | "failed">("idle");

  async function refreshProfile() {
    setStatus("saving");
    try {
      const response = await fetch(
        `${apiBaseUrl}/api/v1/monitoring/models/${trainingRunId}/reference-profile`,
        { method: "POST" },
      );
      if (!response.ok) {
        throw new Error(`Profile refresh failed with status ${response.status}`);
      }
      setStatus("saved");
      router.refresh();
    } catch {
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
        <p className="text-xs text-rose-700">Profile refresh failed. Check backend availability and model artifacts.</p>
      ) : null}
    </div>
  );
}
