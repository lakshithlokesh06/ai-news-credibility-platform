"use client";

import { Archive, RefreshCcw, Trophy } from "lucide-react";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { ExperimentSummary, ModelLifecycleStatus, apiBaseUrl, apiErrorMessage, formatLifecycleStatus } from "@/lib/api";

type LifecycleActionsProps = {
  trainingRunId: string;
  modelName: string;
  lifecycleStatus: ModelLifecycleStatus | null;
  executionStatus: string;
  currentChampion: ExperimentSummary | null;
};

export function LifecycleActions({
  trainingRunId,
  modelName,
  lifecycleStatus,
  executionStatus,
  currentChampion,
}: LifecycleActionsProps) {
  const router = useRouter();
  const [message, setMessage] = useState<string | null>(null);
  const [isWorking, setIsWorking] = useState(false);
  const canAct = executionStatus === "completed";

  async function runAction(action: "promote" | "archive" | "restore") {
    setMessage(null);
    if (action === "promote") {
      const current = currentChampion?.model_display_name ?? "no current champion";
      const confirmed = window.confirm(
        `Promote "${modelName}" to champion?\n\nCurrent champion: ${current}\nProposed champion: ${modelName}`,
      );
      if (!confirmed) {
        return;
      }
    }
    if (action === "archive") {
      const confirmed = window.confirm(
        `Archive "${modelName}"?\n\nArchived models remain in history and experiments but cannot be the active champion.`,
      );
      if (!confirmed) {
        return;
      }
    }
    setIsWorking(true);
    try {
      const response = await fetch(`${apiBaseUrl}/api/v1/models/${trainingRunId}/${action}`, {
        method: "POST",
      });
      const payload = await response.json();
      if (!response.ok) {
        setMessage(apiErrorMessage(payload, "Lifecycle action failed."));
        return;
      }
      setMessage(payload.message ?? "Lifecycle updated.");
      router.refresh();
    } catch {
      setMessage("Backend lifecycle API is not reachable.");
    } finally {
      setIsWorking(false);
    }
  }

  return (
    <div className="grid gap-3">
      <button
        type="button"
        onClick={() => runAction("promote")}
        disabled={!canAct || lifecycleStatus === "champion" || isWorking}
        className="inline-flex items-center justify-center gap-2 rounded-md bg-ink px-4 py-2 text-sm font-semibold text-white disabled:cursor-not-allowed disabled:bg-slate-300"
      >
        <Trophy aria-hidden="true" className="h-4 w-4" />
        Promote champion
      </button>
      {lifecycleStatus === "archived" ? (
        <button
          type="button"
          onClick={() => runAction("restore")}
          disabled={!canAct || isWorking}
          className="inline-flex items-center justify-center gap-2 rounded-md border border-slate-300 px-4 py-2 text-sm font-semibold text-ink disabled:cursor-not-allowed disabled:text-slate-400"
        >
          <RefreshCcw aria-hidden="true" className="h-4 w-4" />
          Restore candidate
        </button>
      ) : (
        <button
          type="button"
          onClick={() => runAction("archive")}
          disabled={!canAct || lifecycleStatus === "champion" || isWorking}
          className="inline-flex items-center justify-center gap-2 rounded-md border border-slate-300 px-4 py-2 text-sm font-semibold text-ink disabled:cursor-not-allowed disabled:text-slate-400"
        >
          <Archive aria-hidden="true" className="h-4 w-4" />
          Archive
        </button>
      )}
      <p className="text-xs leading-5 text-slate-500">
        Current lifecycle: {formatLifecycleStatus(lifecycleStatus)}
      </p>
      {message ? <p className="rounded-md bg-slate-50 px-3 py-2 text-xs leading-5 text-slate-700">{message}</p> : null}
    </div>
  );
}
