import Link from "next/link";
import { ArrowLeft, FileText } from "lucide-react";

import { DeleteHistoryButton } from "@/components/DeleteHistoryButton";
import { EmptyState } from "@/components/EmptyState";
import { PageHeader } from "@/components/PageHeader";
import {
  AnalysisHistoryDetail,
  InfluentialItem,
  fetchFromApi,
  formatExplanationMethod,
  formatMetric,
  formatModelFamily,
  formatModelType,
} from "@/lib/api";

export const dynamic = "force-dynamic";

type HistoryDetailPageProps = {
  params: Promise<{ analysisId: string }>;
};

async function loadAnalysis(analysisId: string) {
  try {
    return await fetchFromApi<AnalysisHistoryDetail>(`/api/v1/history/${analysisId}`);
  } catch {
    return null;
  }
}

export default async function HistoryDetailPage({ params }: HistoryDetailPageProps) {
  const { analysisId } = await params;
  const analysis = await loadAnalysis(analysisId);

  if (!analysis) {
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
            <p className="text-xl font-semibold text-ink">
              {analysis.predicted_label === "FAKE" ? "Likely misinformation" : "Likely credible"}
            </p>
            <p>REAL probability: {formatMetric(analysis.real_probability)}</p>
            <p>FAKE probability: {formatMetric(analysis.fake_probability)}</p>
            <p>Confidence: {formatMetric(analysis.confidence)}</p>
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
                <InfluenceList title="Influences toward likely misinformation" items={analysis.explanation.influences_toward_fake} tone="fake" />
                <InfluenceList title="Influences toward likely credible" items={analysis.explanation.influences_toward_real} tone="real" />
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
      </div>
    </>
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
        <p className="mt-4 text-sm leading-6 text-slate-500">No saved local evidence in this direction.</p>
      )}
    </div>
  );
}
