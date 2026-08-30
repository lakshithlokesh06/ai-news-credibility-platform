"use client";

import { Trash2 } from "lucide-react";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { apiBaseUrl } from "@/lib/api";

export function DeleteHistoryButton({ analysisId }: { analysisId: string }) {
  const router = useRouter();
  const [confirming, setConfirming] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function deleteAnalysis() {
    if (!confirming) {
      setConfirming(true);
      return;
    }
    setIsDeleting(true);
    setError(null);
    try {
      const response = await fetch(`${apiBaseUrl}/api/v1/history/${analysisId}`, {
        method: "DELETE",
      });
      if (!response.ok) {
        setError("Could not delete this saved analysis.");
        return;
      }
      router.push("/history");
      router.refresh();
    } catch {
      setError("Backend history API is not reachable.");
    } finally {
      setIsDeleting(false);
    }
  }

  return (
    <div className="grid gap-2">
      <button
        type="button"
        onClick={deleteAnalysis}
        disabled={isDeleting}
        className={
          confirming
            ? "inline-flex items-center justify-center gap-2 rounded-md bg-rose-700 px-4 py-2 text-sm font-semibold text-white disabled:bg-slate-300"
            : "inline-flex items-center justify-center gap-2 rounded-md border border-rose-200 px-4 py-2 text-sm font-semibold text-rose-700 disabled:text-slate-400"
        }
      >
        <Trash2 aria-hidden="true" className="h-4 w-4" />
        {confirming ? "Confirm delete" : "Delete analysis"}
      </button>
      {confirming ? (
        <button
          type="button"
          onClick={() => setConfirming(false)}
          className="text-sm font-medium text-slate-500"
        >
          Cancel deletion
        </button>
      ) : null}
      {error ? <p className="text-sm leading-6 text-rose-700">{error}</p> : null}
    </div>
  );
}
