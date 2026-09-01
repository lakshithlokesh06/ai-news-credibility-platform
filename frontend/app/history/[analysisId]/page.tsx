import Link from "next/link";
import { ArrowLeft, ClipboardCheck, FileText, UserCheck } from "lucide-react";

import { DeleteHistoryButton } from "@/components/DeleteHistoryButton";
import { EmptyState } from "@/components/EmptyState";
import { HumanReviewForm } from "@/components/HumanReviewForm";
import { PageHeader } from "@/components/PageHeader";
import {
  AnalysisHistoryDetail,
  AnalysisEvidenceSummary,
  InfluentialItem,
  fetchFromApi,
  formatExplanationMethod,
  formatMetric,
  formatModelFamily,
  formatModelType,
  formatReviewedLabel,
  formatReviewStatus,
} from "@/lib/api";

export const dynamic = "force-dynamic";

type HistoryDetailPageProps = {
  params: Promise<{ analysisId: string }>;
};

async function loadAnalysis(analysisId: string) {
  try {
    const [analysis, evidenceSummary] = await Promise.all([
      fetchFromApi<AnalysisHistoryDetail>(`/api/v1/history/${analysisId}`),
      fetchFromApi<AnalysisEvidenceSummary>(`/api/v1/history/${analysisId}/evidence-summary`),
    ]);
    return { analysis, evidenceSummary };
  } catch {
    return null;
  }
}

export default async function HistoryDetailPage({ params }: HistoryDetailPageProps) {
  const { analysisId } = await params;
  const data = await loadAnalysis(analysisId);

  if (!data) {
    return (
      <>
        <PageHeader
          eyebrow="Saved analysis"
          title="History detail"
          description="This saved analysis could not be found."
        />
        <div className="mx-auto w-full max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
          <EmptyState
            icon={FileText}
            title="Analysis not found"
            description="The saved analysis may have been deleted, or the history API may be unavailable."
          />
        </div>
      </>
    );
  }

  const analysis = data.analysis;
  const evidenceSummary = data.evidenceSummary;

  return (
    <>
      <PageHeader
        eyebrow="Saved analysis"
        title={analysis.title || "Untitled analysis"}
        description="A persisted prediction and explanation snapshot. This page reads saved data and does not rerun inference or SHAP."
      />
      <div className="mx-auto grid w-full max-w-7xl gap-6 px-4 py-8 sm:px-6 lg:grid-cols-[1fr_340px] lg:px-8">
        <section className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
          <Link href="/history" className="inline-flex items-center gap-2 text-sm font-semibold text-ink">
            <ArrowLeft aria-hidden="true" className="h-4 w-4" />
            Back to history
          </Link>
          <div className="mt-6 grid gap-4">
            <div>
              <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Headline</p>
              <h2 className="mt-2 text-xl font-semibold text-ink">{analysis.title || "Untitled analysis"}</h2>
            </div>
            <div>
              <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Article text</p>
              <p className="mt-2 whitespace-pre-wrap text-sm leading-7 text-slate-700">
                {analysis.content || "No article body was saved for this analysis."}
              </p>
            </div>
          </div>
        </section>

        <aside className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
          <h2 className="text-lg font-semibold text-ink">Prediction snapshot</h2>
          <div className="mt-5 grid gap-3 text-sm text-slate-700">
            <div>
              <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Model Prediction</p>
              <p className="mt-1 text-xl font-semibold text-ink">
                {analysis.predicted_label === "FAKE" ? "Likely misinformation" : "Likely credible"}
              </p>
            </div>
            <p>REAL probability: {formatMetric(analysis.real_probability)}</p>
            <p>FAKE probability: {formatMetric(analysis.fake_probability)}</p>
            <p>Model Confidence: {formatMetric(analysis.confidence)}</p>
            <p>Model family: {formatModelFamily(analysis.model_family)}</p>
            <p>Model: {analysis.model_name ?? formatModelType(analysis.model_type)}</p>
            <p>Training run: {analysis.model_display_name}</p>
            <p>Text mode: {analysis.text_composition_mode ?? "N/A"}</p>
            <p>Analyzed: {new Date(analysis.created_at).toLocaleString()}</p>
          </div>
          <div className="mt-6 border-t border-slate-200 pt-5">
            <DeleteHistoryButton analysisId={analysis.id} />
          </div>
        </aside>

        <section className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm lg:col-span-2">
          <h2 className="text-lg font-semibold text-ink">Persisted explanation</h2>
          {analysis.explanation ? (
            <div className="mt-5 grid gap-5">
              <div className="grid gap-2 text-sm text-slate-700 md:grid-cols-3">
                <p>Method: {formatExplanationMethod(analysis.explanation.explanation_method)}</p>
                <p>Explained class: {analysis.explanation.explained_class}</p>
                <p>Generated: {new Date(analysis.explanation.generated_at).toLocaleString()}</p>
              </div>
              <div className="grid gap-4 lg:grid-cols-2">
                <InfluenceList title="Influenced toward FAKE" items={analysis.explanation.influences_toward_fake} tone="fake" />
                <InfluenceList title="Influenced toward REAL" items={analysis.explanation.influences_toward_real} tone="real" />
              </div>
              <div className="rounded-md bg-slate-50 px-4 py-3 text-sm leading-6 text-slate-600">
                {analysis.explanation.message ? <p>{analysis.explanation.message}</p> : null}
                <ul className="mt-2 list-disc space-y-1 pl-5">
                  {analysis.explanation.limitations.map((limitation) => (
                    <li key={limitation}>{limitation}</li>
                  ))}
                </ul>
              </div>
            </div>
          ) : (
            <p className="mt-4 text-sm leading-6 text-slate-600">
              No explanation was saved with this analysis. Opening history never reruns explanation work.
            </p>
          )}
        </section>

        <section className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm lg:col-span-2">
          <div className="flex items-center gap-2">
            <ClipboardCheck aria-hidden="true" className="h-4 w-4 text-signal" />
            <h2 className="text-lg font-semibold text-ink">Evidence & Claims</h2>
          </div>
          <div className="mt-5 grid gap-4 md:grid-cols-4">
            <MetricCard label="Claims" value={String(evidenceSummary.total_claims)} />
            <MetricCard label="Evidence references" value={String(evidenceSummary.total_evidence_references)} />
            <MetricCard label="Supports" value={String(evidenceSummary.supporting_evidence_count)} />
            <MetricCard label="Contradicts" value={String(evidenceSummary.contradicting_evidence_count)} />
          </div>
          <p className="mt-4 rounded-md bg-slate-50 px-4 py-3 text-sm leading-6 text-slate-600">
            Evidence coverage is a workflow metric, not a credibility score. Evidence does not automatically determine the verified label.
          </p>
          <Link
            href={`/history/${analysis.id}/evidence`}
            className="mt-5 inline-flex items-center justify-center rounded-md bg-ink px-4 py-2 text-sm font-semibold text-white"
          >
            Open evidence workspace
          </Link>
        </section>

        <section className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm lg:col-span-2">
          <div className="flex items-center gap-2">
            <UserCheck aria-hidden="true" className="h-4 w-4 text-signal" />
            <h2 className="text-lg font-semibold text-ink">Human Review</h2>
          </div>
          <div className="mt-5 grid gap-5 lg:grid-cols-[1fr_1.2fr]">
            <div className="rounded-lg border border-slate-200 bg-surface p-5">
              <dl className="grid gap-3 text-sm">
                <Definition
                  label="Model prediction"
                  value={analysis.predicted_label === "FAKE" ? "Likely misinformation" : "Likely credible"}
                />
                <Definition label="Human-verified label" value={formatReviewedLabel(analysis.review.verified_label)} />
                <Definition label="Review status" value={formatReviewStatus(analysis.review)} />
                <Definition
                  label="Prediction match"
                  value={
                    analysis.review.is_prediction_correct === null
                      ? "N/A"
                      : analysis.review.is_prediction_correct
                        ? "Matched reviewed label"
                        : "Did not match reviewed label"
                  }
                />
                <Definition
                  label="Reviewed"
                  value={analysis.review.reviewed_at ? new Date(analysis.review.reviewed_at).toLocaleString() : "N/A"}
                />
              </dl>
            </div>
            <HumanReviewForm
              analysisId={analysis.id}
              predictedLabel={analysis.predicted_label}
              review={analysis.review}
              evidenceSummary={evidenceSummary}
              showNotes
            />
          </div>
        </section>
      </div>
    </>
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

function MetricCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg border border-slate-200 bg-surface p-4">
      <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">{label}</p>
      <p className="mt-2 text-2xl font-semibold text-ink">{value}</p>
    </div>
  );
}

function InfluenceList({
  title,
  items,
  tone,
}: {
  title: string;
  items: InfluentialItem[];
  tone: "fake" | "real";
}) {
  const maxMagnitude = Math.max(...items.map((item) => item.attribution_magnitude), 0.000001);
  const toneClasses =
    tone === "fake"
      ? "border-rose-200 bg-rose-50 text-rose-950"
      : "border-emerald-200 bg-emerald-50 text-emerald-950";

  return (
    <div className="rounded-md border border-slate-200 p-4">
      <h3 className="text-sm font-semibold text-ink">{title}</h3>
      {items.length ? (
        <div className="mt-4 grid gap-3">
          {items.map((item) => (
            <div key={`${item.direction}-${item.rank}-${item.text}`} className="grid gap-2">
              <div className="flex items-center justify-between gap-3">
                <span className={`rounded-md border px-2 py-1 text-sm font-medium ${toneClasses}`}>{item.text}</span>
                <span className="text-xs text-slate-500">Rank {item.rank}</span>
              </div>
              <div className="h-2 rounded-full bg-slate-100">
                <div
                  className={tone === "fake" ? "h-2 rounded-full bg-rose-500" : "h-2 rounded-full bg-emerald-500"}
                  style={{ width: `${Math.max(8, (item.attribution_magnitude / maxMagnitude) * 100)}%` }}
                />
              </div>
            </div>
          ))}
        </div>
      ) : (
        <p className="mt-4 text-sm leading-6 text-slate-500">No saved model influence in this direction.</p>
      )}
    </div>
  );
}
