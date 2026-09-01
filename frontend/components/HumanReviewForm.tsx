"use client";

import { Check, RotateCcw, Save, Trash2 } from "lucide-react";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { AnalysisEvidenceSummary, AnalysisReviewInfo, ArticleLabel, apiBaseUrl, apiErrorMessage } from "@/lib/api";

type HumanReviewFormProps = {
  analysisId: string;
  predictedLabel: ArticleLabel;
  review: AnalysisReviewInfo;
  showNotes?: boolean;
  evidenceSummary?: AnalysisEvidenceSummary | null;
};

export function HumanReviewForm({ analysisId, predictedLabel, review, showNotes = false, evidenceSummary }: HumanReviewFormProps) {
  const router = useRouter();
  const [selectedLabel, setSelectedLabel] = useState<ArticleLabel>(review.verified_label ?? predictedLabel);
  const [reviewerNote, setReviewerNote] = useState(review.reviewer_note ?? "");
  const [evidenceNote, setEvidenceNote] = useState(review.evidence_note ?? "");
  const [pendingChange, setPendingChange] = useState<ArticleLabel | null>(null);
  const [confirmDelete, setConfirmDelete] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const hasReview = review.status === "reviewed";
  const isChangingLabel = hasReview && review.verified_label !== selectedLabel;

  async function saveReview() {
    if (isChangingLabel && pendingChange !== selectedLabel) {
      setPendingChange(selectedLabel);
      return;
    }
    setIsSaving(true);
    setError(null);
    try {
      const response = await fetch(`${apiBaseUrl}/api/v1/history/${analysisId}/review`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          verified_label: selectedLabel,
          reviewer_note: showNotes ? reviewerNote : null,
          evidence_note: showNotes ? evidenceNote : null,
        }),
      });
      const payload = await response.json();
      if (!response.ok) {
        setError(apiErrorMessage(payload, "Could not save the human review."));
        return;
      }
      setPendingChange(null);
      router.refresh();
    } catch {
      setError("Backend review API is not reachable.");
    } finally {
      setIsSaving(false);
    }
  }

  async function deleteReview() {
    if (!confirmDelete) {
      setConfirmDelete(true);
      return;
    }
    setIsSaving(true);
    setError(null);
    try {
      const response = await fetch(`${apiBaseUrl}/api/v1/history/${analysisId}/review`, {
        method: "DELETE",
      });
      const payload = await response.json();
      if (!response.ok) {
        setError(apiErrorMessage(payload, "Could not remove the human review."));
        return;
      }
      setConfirmDelete(false);
      router.refresh();
    } catch {
      setError("Backend review API is not reachable.");
    } finally {
      setIsSaving(false);
    }
  }

  return (
    <div className="grid gap-4">
      <div className="grid grid-cols-2 gap-2">
        <button
          type="button"
          onClick={() => {
            setSelectedLabel("REAL");
            setPendingChange(null);
          }}
          className={labelButtonClass(selectedLabel === "REAL", "REAL")}
        >
          <Check aria-hidden="true" className="h-4 w-4" />
          REAL
        </button>
        <button
          type="button"
          onClick={() => {
            setSelectedLabel("FAKE");
            setPendingChange(null);
          }}
          className={labelButtonClass(selectedLabel === "FAKE", "FAKE")}
        >
          <Check aria-hidden="true" className="h-4 w-4" />
          FAKE
        </button>
      </div>

      {showNotes ? (
        <div className="grid gap-3">
          <label className="grid gap-2">
            <span className="text-xs font-semibold uppercase tracking-wide text-slate-500">Reviewer note</span>
            <textarea
              value={reviewerNote}
              onChange={(event) => setReviewerNote(event.target.value)}
              maxLength={1000}
              rows={3}
              className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm leading-6 text-slate-700"
            />
          </label>
          <label className="grid gap-2">
            <span className="text-xs font-semibold uppercase tracking-wide text-slate-500">Evidence/reference note</span>
            <textarea
              value={evidenceNote}
              onChange={(event) => setEvidenceNote(event.target.value)}
              maxLength={2000}
              rows={3}
              className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm leading-6 text-slate-700"
            />
          </label>
        </div>
      ) : null}

      {evidenceSummary ? (
        <div className="rounded-md bg-slate-50 px-3 py-2 text-sm leading-6 text-slate-600">
          <p>
            Claims: {evidenceSummary.total_claims} / Evidence references: {evidenceSummary.total_evidence_references}
          </p>
          <p>
            Supports: {evidenceSummary.supporting_evidence_count} / Contradicts: {evidenceSummary.contradicting_evidence_count} / Neutral: {evidenceSummary.neutral_evidence_count + evidenceSummary.unclear_evidence_count}
          </p>
          {evidenceSummary.total_evidence_references > 0 ? (
            <p className="mt-1 text-slate-500">
              You have recorded evidence for this analysis. The verified label remains your manual judgment.
            </p>
          ) : null}
        </div>
      ) : null}

      {pendingChange ? (
        <p className="rounded-md bg-amber-50 px-3 py-2 text-sm leading-6 text-amber-900">
          Confirm changing the human-verified label from {review.verified_label} to {pendingChange}.
        </p>
      ) : null}

      <div className="flex flex-wrap gap-2">
        <button
          type="button"
          onClick={saveReview}
          disabled={isSaving}
          className="inline-flex items-center justify-center gap-2 rounded-md bg-ink px-4 py-2 text-sm font-semibold text-white disabled:bg-slate-300"
        >
          <Save aria-hidden="true" className="h-4 w-4" />
          {hasReview ? "Update review" : "Save review"}
        </button>
        {hasReview ? (
          <button
            type="button"
            onClick={deleteReview}
            disabled={isSaving}
            className={
              confirmDelete
                ? "inline-flex items-center justify-center gap-2 rounded-md bg-rose-700 px-4 py-2 text-sm font-semibold text-white disabled:bg-slate-300"
                : "inline-flex items-center justify-center gap-2 rounded-md border border-rose-200 px-4 py-2 text-sm font-semibold text-rose-700 disabled:text-slate-400"
            }
          >
            <Trash2 aria-hidden="true" className="h-4 w-4" />
            {confirmDelete ? "Confirm remove" : "Remove review"}
          </button>
        ) : null}
        {confirmDelete || pendingChange ? (
          <button
            type="button"
            onClick={() => {
              setConfirmDelete(false);
              setPendingChange(null);
              setSelectedLabel(review.verified_label ?? predictedLabel);
            }}
            className="inline-flex items-center justify-center gap-2 rounded-md border border-slate-300 px-4 py-2 text-sm font-semibold text-ink"
          >
            <RotateCcw aria-hidden="true" className="h-4 w-4" />
            Cancel
          </button>
        ) : null}
      </div>
      {error ? <p className="text-sm leading-6 text-rose-700">{error}</p> : null}
    </div>
  );
}

function labelButtonClass(active: boolean, label: ArticleLabel) {
  if (active && label === "REAL") {
    return "inline-flex items-center justify-center gap-2 rounded-md border border-emerald-300 bg-emerald-50 px-3 py-2 text-sm font-semibold text-emerald-800";
  }
  if (active) {
    return "inline-flex items-center justify-center gap-2 rounded-md border border-rose-300 bg-rose-50 px-3 py-2 text-sm font-semibold text-rose-800";
  }
  return "inline-flex items-center justify-center gap-2 rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold text-slate-700";
}
