"use client";

import { ExternalLink, Pencil, Plus, Save, Trash2 } from "lucide-react";
import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";

import {
  AnalysisClaim,
  AnalysisEvidenceSummary,
  AnalysisHistoryDetail,
  EvidenceAssessment,
  EvidenceReference,
  apiBaseUrl,
  apiErrorMessage,
  formatEvidenceAssessment,
  formatMetric,
  formatReviewedLabel,
  formatReviewStatus,
} from "@/lib/api";

type EvidenceWorkspaceClientProps = {
  analysis: AnalysisHistoryDetail;
  claims: AnalysisClaim[];
  summary: AnalysisEvidenceSummary;
};

const emptyEvidence = {
  source_url: "",
  source_title: "",
  publisher: "",
  publication_date: "",
  assessment: "supports" as EvidenceAssessment,
  evidence_excerpt: "",
  reviewer_note: "",
};

export function EvidenceWorkspaceClient({ analysis, claims, summary }: EvidenceWorkspaceClientProps) {
  const router = useRouter();
  const [claimText, setClaimText] = useState("");
  const [claimNote, setClaimNote] = useState("");
  const [editingClaimId, setEditingClaimId] = useState<string | null>(null);
  const [claimDraft, setClaimDraft] = useState({ claim_text: "", reviewer_note: "", status: "open" });
  const [evidenceDrafts, setEvidenceDrafts] = useState<Record<string, typeof emptyEvidence>>({});
  const [editingEvidenceId, setEditingEvidenceId] = useState<string | null>(null);
  const [evidenceEditDraft, setEvidenceEditDraft] = useState(emptyEvidence);
  const [confirmDeleteClaimId, setConfirmDeleteClaimId] = useState<string | null>(null);
  const [confirmDeleteEvidenceId, setConfirmDeleteEvidenceId] = useState<string | null>(null);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function submitClaim(event: FormEvent) {
    event.preventDefault();
    await mutate(`/api/v1/history/${analysis.id}/claims`, {
      method: "POST",
      body: {
        claim_text: claimText,
        reviewer_note: claimNote || null,
      },
      onSuccess: () => {
        setClaimText("");
        setClaimNote("");
      },
    });
  }

  async function saveClaim(claim: AnalysisClaim) {
    await mutate(`/api/v1/claims/${claim.id}`, {
      method: "PATCH",
      body: {
        claim_text: claimDraft.claim_text,
        reviewer_note: claimDraft.reviewer_note || null,
        status: claimDraft.status,
      },
      onSuccess: () => setEditingClaimId(null),
    });
  }

  async function deleteClaim(claim: AnalysisClaim) {
    if (confirmDeleteClaimId !== claim.id) {
      setConfirmDeleteClaimId(claim.id);
      return;
    }
    await mutate(`/api/v1/claims/${claim.id}`, {
      method: "DELETE",
      onSuccess: () => setConfirmDeleteClaimId(null),
    });
  }

  async function saveEvidence(claimId: string) {
    const draft = evidenceDrafts[claimId] ?? emptyEvidence;
    await mutate(`/api/v1/claims/${claimId}/evidence`, {
      method: "POST",
      body: evidencePayload(draft),
      onSuccess: () => setEvidenceDrafts((current) => ({ ...current, [claimId]: emptyEvidence })),
    });
  }

  async function updateEvidence(evidence: EvidenceReference) {
    await mutate(`/api/v1/evidence/${evidence.id}`, {
      method: "PATCH",
      body: evidencePayload(evidenceEditDraft),
      onSuccess: () => setEditingEvidenceId(null),
    });
  }

  async function deleteEvidence(evidence: EvidenceReference) {
    if (confirmDeleteEvidenceId !== evidence.id) {
      setConfirmDeleteEvidenceId(evidence.id);
      return;
    }
    await mutate(`/api/v1/evidence/${evidence.id}`, {
      method: "DELETE",
      onSuccess: () => setConfirmDeleteEvidenceId(null),
    });
  }

  async function mutate(
    path: string,
    options: { method: string; body?: unknown; onSuccess?: () => void }
  ) {
    setIsSaving(true);
    setError(null);
    try {
      const response = await fetch(`${apiBaseUrl}${path}`, {
        method: options.method,
        headers: options.body ? { "Content-Type": "application/json" } : undefined,
        body: options.body ? JSON.stringify(options.body) : undefined,
      });
      const payload = await response.json();
      if (!response.ok) {
        setError(apiErrorMessage(payload, "Evidence workspace action failed."));
        return;
      }
      options.onSuccess?.();
      router.refresh();
    } catch {
      setError("Backend evidence API is not reachable.");
    } finally {
      setIsSaving(false);
    }
  }

  return (
    <div className="grid gap-6">
      {error ? (
        <section className="rounded-lg border border-rose-200 bg-rose-50 px-5 py-4 text-sm leading-6 text-rose-900">
          {error}
        </section>
      ) : null}

      <section className="grid gap-4 md:grid-cols-4">
        <MetricCard label="Claims" value={String(summary.total_claims)} />
        <MetricCard label="Evidence references" value={String(summary.total_evidence_references)} />
        <MetricCard label="Evidence coverage" value={summary.evidence_coverage_percentage === null ? "N/A" : `${summary.evidence_coverage_percentage.toFixed(1)}%`} />
        <MetricCard
          label="Review status"
          value={formatReviewStatus(analysis.review)}
          helper={formatReviewedLabel(analysis.review.verified_label)}
        />
      </section>

      <section className="grid gap-6 lg:grid-cols-[1fr_340px]">
        <article className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
          <h2 className="text-lg font-semibold text-ink">Article context</h2>
          <h3 className="mt-4 text-xl font-semibold text-ink">{analysis.title || "Untitled analysis"}</h3>
          <p className="mt-3 max-h-96 overflow-auto whitespace-pre-wrap text-sm leading-7 text-slate-700">
            {analysis.content || "No article body was saved for this analysis."}
          </p>
        </article>
        <aside className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
          <h2 className="text-lg font-semibold text-ink">Model context</h2>
          <dl className="mt-5 grid gap-3 text-sm">
            <Definition label="Prediction" value={analysis.predicted_label} />
            <Definition label="Confidence" value={formatMetric(analysis.confidence)} />
            <Definition label="REAL probability" value={formatMetric(analysis.real_probability)} />
            <Definition label="FAKE probability" value={formatMetric(analysis.fake_probability)} />
            <Definition label="Model" value={analysis.model_display_name} />
          </dl>
          <p className="mt-5 rounded-md bg-slate-50 px-3 py-2 text-sm leading-6 text-slate-600">
            Model explanations show what influenced the classifier. They are not factual evidence.
          </p>
        </aside>
      </section>

      <section className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
        <h2 className="text-lg font-semibold text-ink">Add manual claim</h2>
        <form onSubmit={submitClaim} className="mt-5 grid gap-4">
          <label className="grid gap-2">
            <span className="text-xs font-semibold uppercase tracking-wide text-slate-500">Claim text</span>
            <textarea
              value={claimText}
              onChange={(event) => setClaimText(event.target.value)}
              rows={3}
              required
              className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm leading-6 text-slate-700"
            />
          </label>
          <label className="grid gap-2">
            <span className="text-xs font-semibold uppercase tracking-wide text-slate-500">Reviewer note</span>
            <textarea
              value={claimNote}
              onChange={(event) => setClaimNote(event.target.value)}
              rows={2}
              className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm leading-6 text-slate-700"
            />
          </label>
          <button disabled={isSaving} className="inline-flex w-fit items-center gap-2 rounded-md bg-ink px-4 py-2 text-sm font-semibold text-white disabled:bg-slate-300">
            <Plus aria-hidden="true" className="h-4 w-4" />
            Add claim
          </button>
        </form>
      </section>

      <section className="grid gap-4">
        <h2 className="text-lg font-semibold text-ink">Claims and evidence</h2>
        {claims.length === 0 ? (
          <div className="rounded-lg border border-slate-200 bg-white p-6 text-sm leading-6 text-slate-600 shadow-sm">
            No claims have been manually identified for this analysis.
          </div>
        ) : (
          claims.map((claim) => (
            <ClaimPanel
              key={claim.id}
              claim={claim}
              isSaving={isSaving}
              editingClaimId={editingClaimId}
              claimDraft={claimDraft}
              setClaimDraft={setClaimDraft}
              startEditingClaim={() => {
                setEditingClaimId(claim.id);
                setClaimDraft({
                  claim_text: claim.claim_text,
                  reviewer_note: claim.reviewer_note ?? "",
                  status: claim.status,
                });
              }}
              saveClaim={() => saveClaim(claim)}
              deleteClaim={() => deleteClaim(claim)}
              confirmDeleteClaim={confirmDeleteClaimId === claim.id}
              cancelClaimEdit={() => {
                setEditingClaimId(null);
                setConfirmDeleteClaimId(null);
              }}
              evidenceDraft={evidenceDrafts[claim.id] ?? emptyEvidence}
              setEvidenceDraft={(draft) => setEvidenceDrafts((current) => ({ ...current, [claim.id]: draft }))}
              saveEvidence={() => saveEvidence(claim.id)}
              editingEvidenceId={editingEvidenceId}
              evidenceEditDraft={evidenceEditDraft}
              setEvidenceEditDraft={setEvidenceEditDraft}
              startEditingEvidence={(evidence) => {
                setEditingEvidenceId(evidence.id);
                setEvidenceEditDraft({
                  source_url: evidence.source_url,
                  source_title: evidence.source_title ?? "",
                  publisher: evidence.publisher ?? "",
                  publication_date: evidence.publication_date?.slice(0, 10) ?? "",
                  assessment: evidence.assessment,
                  evidence_excerpt: evidence.evidence_excerpt ?? "",
                  reviewer_note: evidence.reviewer_note ?? "",
                });
              }}
              updateEvidence={updateEvidence}
              deleteEvidence={deleteEvidence}
              confirmDeleteEvidenceId={confirmDeleteEvidenceId}
              cancelEvidenceEdit={() => {
                setEditingEvidenceId(null);
                setConfirmDeleteEvidenceId(null);
              }}
            />
          ))
        )}
      </section>
    </div>
  );
}

function ClaimPanel({
  claim,
  isSaving,
  editingClaimId,
  claimDraft,
  setClaimDraft,
  startEditingClaim,
  saveClaim,
  deleteClaim,
  confirmDeleteClaim,
  cancelClaimEdit,
  evidenceDraft,
  setEvidenceDraft,
  saveEvidence,
  editingEvidenceId,
  evidenceEditDraft,
  setEvidenceEditDraft,
  startEditingEvidence,
  updateEvidence,
  deleteEvidence,
  confirmDeleteEvidenceId,
  cancelEvidenceEdit,
}: {
  claim: AnalysisClaim;
  isSaving: boolean;
  editingClaimId: string | null;
  claimDraft: { claim_text: string; reviewer_note: string; status: string };
  setClaimDraft: (draft: { claim_text: string; reviewer_note: string; status: string }) => void;
  startEditingClaim: () => void;
  saveClaim: () => void;
  deleteClaim: () => void;
  confirmDeleteClaim: boolean;
  cancelClaimEdit: () => void;
  evidenceDraft: typeof emptyEvidence;
  setEvidenceDraft: (draft: typeof emptyEvidence) => void;
  saveEvidence: () => void;
  editingEvidenceId: string | null;
  evidenceEditDraft: typeof emptyEvidence;
  setEvidenceEditDraft: (draft: typeof emptyEvidence) => void;
  startEditingEvidence: (evidence: EvidenceReference) => void;
  updateEvidence: (evidence: EvidenceReference) => void;
  deleteEvidence: (evidence: EvidenceReference) => void;
  confirmDeleteEvidenceId: string | null;
  cancelEvidenceEdit: () => void;
}) {
  const isEditing = editingClaimId === claim.id;
  return (
    <article className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
      <div className="grid gap-4 lg:grid-cols-[1fr_auto]">
        <div>
          {isEditing ? (
            <div className="grid gap-3">
              <label className="grid gap-2">
                <span className="text-xs font-semibold uppercase tracking-wide text-slate-500">Claim text</span>
                <textarea
                  value={claimDraft.claim_text}
                  onChange={(event) => setClaimDraft({ ...claimDraft, claim_text: event.target.value })}
                  rows={3}
                  className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm leading-6 text-slate-700"
                />
              </label>
              <label className="grid gap-2">
                <span className="text-xs font-semibold uppercase tracking-wide text-slate-500">Status</span>
                <select
                  value={claimDraft.status}
                  onChange={(event) => setClaimDraft({ ...claimDraft, status: event.target.value })}
                  className="h-10 rounded-md border border-slate-300 bg-white px-3 text-sm text-slate-700"
                >
                  <option value="open">Open</option>
                  <option value="reviewed">Reviewed</option>
                </select>
              </label>
              <label className="grid gap-2">
                <span className="text-xs font-semibold uppercase tracking-wide text-slate-500">Reviewer note</span>
                <textarea
                  value={claimDraft.reviewer_note}
                  onChange={(event) => setClaimDraft({ ...claimDraft, reviewer_note: event.target.value })}
                  rows={2}
                  className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm leading-6 text-slate-700"
                />
              </label>
            </div>
          ) : (
            <>
              <div className="flex flex-wrap items-center gap-2">
                <span className="rounded-md bg-slate-100 px-2 py-1 text-xs font-medium text-slate-600">
                  {claim.status === "reviewed" ? "Claim reviewed" : "Claim open"}
                </span>
                <EvidenceBadge assessment="supports" count={claim.evidence_counts.supports} />
                <EvidenceBadge assessment="contradicts" count={claim.evidence_counts.contradicts} />
                <EvidenceBadge assessment="neutral" count={claim.evidence_counts.neutral + claim.evidence_counts.unclear} />
              </div>
              <p className="mt-3 text-base font-semibold leading-7 text-ink">{claim.claim_text}</p>
              {claim.reviewer_note ? <p className="mt-2 text-sm leading-6 text-slate-600">{claim.reviewer_note}</p> : null}
            </>
          )}
        </div>
        <div className="flex flex-wrap items-start gap-2">
          {isEditing ? (
            <>
              <button type="button" onClick={saveClaim} disabled={isSaving} className="inline-flex items-center gap-2 rounded-md bg-ink px-3 py-2 text-sm font-semibold text-white disabled:bg-slate-300">
                <Save aria-hidden="true" className="h-4 w-4" />
                Save
              </button>
              <button type="button" onClick={cancelClaimEdit} className="rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold text-ink">
                Cancel
              </button>
            </>
          ) : (
            <>
              <button type="button" onClick={startEditingClaim} className="inline-flex items-center gap-2 rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold text-ink">
                <Pencil aria-hidden="true" className="h-4 w-4" />
                Edit
              </button>
              <button
                type="button"
                onClick={deleteClaim}
                disabled={isSaving}
                className={confirmDeleteClaim ? "inline-flex items-center gap-2 rounded-md bg-rose-700 px-3 py-2 text-sm font-semibold text-white disabled:bg-slate-300" : "inline-flex items-center gap-2 rounded-md border border-rose-200 px-3 py-2 text-sm font-semibold text-rose-700 disabled:text-slate-400"}
              >
                <Trash2 aria-hidden="true" className="h-4 w-4" />
                {confirmDeleteClaim ? "Confirm delete claim and evidence" : "Delete"}
              </button>
            </>
          )}
        </div>
      </div>

      <div className="mt-6 grid gap-4 border-t border-slate-200 pt-5">
        <EvidenceForm draft={evidenceDraft} setDraft={setEvidenceDraft} onSave={saveEvidence} isSaving={isSaving} mode="create" />
        {claim.evidence.length === 0 ? (
          <p className="rounded-md bg-slate-50 px-4 py-3 text-sm leading-6 text-slate-600">
            No evidence references have been recorded for this claim.
          </p>
        ) : (
          <div className="grid gap-3">
            {claim.evidence.map((evidence) => (
              <EvidenceCard
                key={evidence.id}
                evidence={evidence}
                isEditing={editingEvidenceId === evidence.id}
                draft={evidenceEditDraft}
                setDraft={setEvidenceEditDraft}
                startEditing={() => startEditingEvidence(evidence)}
                save={() => updateEvidence(evidence)}
                deleteEvidence={() => deleteEvidence(evidence)}
                confirmDelete={confirmDeleteEvidenceId === evidence.id}
                cancel={cancelEvidenceEdit}
                isSaving={isSaving}
              />
            ))}
          </div>
        )}
      </div>
    </article>
  );
}

function EvidenceForm({
  draft,
  setDraft,
  onSave,
  isSaving,
  mode,
}: {
  draft: typeof emptyEvidence;
  setDraft: (draft: typeof emptyEvidence) => void;
  onSave: () => void;
  isSaving: boolean;
  mode: "create" | "edit";
}) {
  const isEditing = mode === "edit";
  return (
    <div className="rounded-lg border border-slate-200 bg-surface p-4">
      <h3 className="text-sm font-semibold text-ink">{isEditing ? "Edit evidence reference" : "Add evidence reference"}</h3>
      <div className="mt-4 grid gap-3 md:grid-cols-2">
        <TextInput label="Source URL" value={draft.source_url} onChange={(value) => setDraft({ ...draft, source_url: value })} required />
        <TextInput label="Source title" value={draft.source_title} onChange={(value) => setDraft({ ...draft, source_title: value })} />
        <TextInput label="Publisher/source" value={draft.publisher} onChange={(value) => setDraft({ ...draft, publisher: value })} />
        <TextInput label="Publication date" type="date" value={draft.publication_date} onChange={(value) => setDraft({ ...draft, publication_date: value })} />
        <label className="grid gap-2">
          <span className="text-xs font-semibold uppercase tracking-wide text-slate-500">Assessment</span>
          <select value={draft.assessment} onChange={(event) => setDraft({ ...draft, assessment: event.target.value as EvidenceAssessment })} className="h-10 rounded-md border border-slate-300 bg-white px-3 text-sm text-slate-700">
            <option value="supports">Supports claim</option>
            <option value="contradicts">Contradicts claim</option>
            <option value="neutral">Neutral</option>
            <option value="unclear">Unclear</option>
          </select>
        </label>
        <div />
        <TextArea label="Evidence excerpt" value={draft.evidence_excerpt} onChange={(value) => setDraft({ ...draft, evidence_excerpt: value })} />
        <TextArea label="Reviewer note" value={draft.reviewer_note} onChange={(value) => setDraft({ ...draft, reviewer_note: value })} />
      </div>
      <button type="button" onClick={onSave} disabled={isSaving} className="mt-4 inline-flex items-center gap-2 rounded-md bg-ink px-4 py-2 text-sm font-semibold text-white disabled:bg-slate-300">
        {isEditing ? <Save aria-hidden="true" className="h-4 w-4" /> : <Plus aria-hidden="true" className="h-4 w-4" />}
        {isEditing ? "Save evidence" : "Add evidence"}
      </button>
    </div>
  );
}

function EvidenceCard({
  evidence,
  isEditing,
  draft,
  setDraft,
  startEditing,
  save,
  deleteEvidence,
  confirmDelete,
  cancel,
  isSaving,
}: {
  evidence: EvidenceReference;
  isEditing: boolean;
  draft: typeof emptyEvidence;
  setDraft: (draft: typeof emptyEvidence) => void;
  startEditing: () => void;
  save: () => void;
  deleteEvidence: () => void;
  confirmDelete: boolean;
  cancel: () => void;
  isSaving: boolean;
}) {
  if (isEditing) {
    return (
      <div className="grid gap-3">
        <EvidenceForm draft={draft} setDraft={setDraft} onSave={save} isSaving={isSaving} mode="edit" />
        <button type="button" onClick={cancel} className="mt-3 rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold text-ink">
          Cancel edit
        </button>
      </div>
    );
  }

  return (
    <article className="rounded-lg border border-slate-200 p-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <AssessmentBadge assessment={evidence.assessment} />
          <h4 className="mt-3 font-semibold text-ink">{evidence.source_title || "Untitled evidence source"}</h4>
          {evidence.publisher ? <p className="mt-1 text-sm text-slate-600">{evidence.publisher}</p> : null}
          <a href={evidence.source_url} target="_blank" rel="noopener noreferrer" className="mt-2 inline-flex max-w-full items-center gap-2 break-all text-sm font-semibold text-ink">
            <ExternalLink aria-hidden="true" className="h-4 w-4 shrink-0" />
            {evidence.source_url}
          </a>
        </div>
        <div className="flex flex-wrap gap-2">
          <button type="button" onClick={startEditing} className="inline-flex items-center gap-2 rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold text-ink">
            <Pencil aria-hidden="true" className="h-4 w-4" />
            Edit
          </button>
          <button
            type="button"
            onClick={deleteEvidence}
            disabled={isSaving}
            className={confirmDelete ? "inline-flex items-center gap-2 rounded-md bg-rose-700 px-3 py-2 text-sm font-semibold text-white disabled:bg-slate-300" : "inline-flex items-center gap-2 rounded-md border border-rose-200 px-3 py-2 text-sm font-semibold text-rose-700 disabled:text-slate-400"}
          >
            <Trash2 aria-hidden="true" className="h-4 w-4" />
            {confirmDelete ? "Confirm delete" : "Delete"}
          </button>
        </div>
      </div>
      {evidence.evidence_excerpt ? <p className="mt-3 rounded-md bg-slate-50 px-3 py-2 text-sm leading-6 text-slate-700">{evidence.evidence_excerpt}</p> : null}
      {evidence.reviewer_note ? <p className="mt-2 text-sm leading-6 text-slate-600">{evidence.reviewer_note}</p> : null}
    </article>
  );
}

function EvidenceBadge({ assessment, count }: { assessment: EvidenceAssessment; count: number }) {
  return (
    <span className="rounded-md bg-slate-100 px-2 py-1 text-xs font-medium text-slate-600">
      {formatEvidenceAssessment(assessment)}: {count}
    </span>
  );
}

function AssessmentBadge({ assessment }: { assessment: EvidenceAssessment }) {
  const classes: Record<EvidenceAssessment, string> = {
    supports: "bg-emerald-50 text-emerald-800",
    contradicts: "bg-rose-50 text-rose-800",
    neutral: "bg-slate-100 text-slate-700",
    unclear: "bg-amber-50 text-amber-800",
  };
  return <span className={`rounded-md px-2 py-1 text-xs font-semibold ${classes[assessment]}`}>{formatEvidenceAssessment(assessment)}</span>;
}

function TextInput({
  label,
  value,
  onChange,
  type = "text",
  required = false,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  type?: string;
  required?: boolean;
}) {
  return (
    <label className="grid gap-2">
      <span className="text-xs font-semibold uppercase tracking-wide text-slate-500">{label}</span>
      <input
        type={type}
        value={value}
        required={required}
        onChange={(event) => onChange(event.target.value)}
        className="h-10 rounded-md border border-slate-300 bg-white px-3 text-sm text-slate-700"
      />
    </label>
  );
}

function TextArea({ label, value, onChange }: { label: string; value: string; onChange: (value: string) => void }) {
  return (
    <label className="grid gap-2">
      <span className="text-xs font-semibold uppercase tracking-wide text-slate-500">{label}</span>
      <textarea value={value} onChange={(event) => onChange(event.target.value)} rows={3} className="rounded-md border border-slate-300 bg-white px-3 py-2 text-sm leading-6 text-slate-700" />
    </label>
  );
}

function MetricCard({ label, value, helper }: { label: string; value: string; helper?: string }) {
  return (
    <div className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
      <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">{label}</p>
      <p className="mt-2 text-2xl font-semibold text-ink">{value}</p>
      {helper ? <p className="mt-1 text-sm text-slate-500">{helper}</p> : null}
    </div>
  );
}

function Definition({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <dt className="text-slate-500">{label}</dt>
      <dd className="mt-1 font-semibold text-ink">{value}</dd>
    </div>
  );
}

function evidencePayload(draft: typeof emptyEvidence) {
  return {
    source_url: draft.source_url,
    source_title: draft.source_title || null,
    publisher: draft.publisher || null,
    publication_date: draft.publication_date || null,
    assessment: draft.assessment,
    evidence_excerpt: draft.evidence_excerpt || null,
    reviewer_note: draft.reviewer_note || null,
  };
}
