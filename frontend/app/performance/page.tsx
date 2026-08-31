import Link from "next/link";
import { AlertTriangle, BarChart3, Gauge, GitCompare, UserCheck } from "lucide-react";

import { EmptyState } from "@/components/EmptyState";
import { PageHeader } from "@/components/PageHeader";
import {
  CalibrationDiagnostics,
  ErrorAnalysis,
  ProductionPerformance,
  ReviewStatistics,
  TrainingRunReviewSummary,
  fetchFromApi,
  formatMetric,
  formatPercentage,
} from "@/lib/api";

export const dynamic = "force-dynamic";

type PerformancePageProps = {
  searchParams?: Promise<Record<string, string | string[] | undefined>>;
};

function firstValue(value: string | string[] | undefined) {
  return Array.isArray(value) ? value[0] : value;
}

async function loadPerformance(trainingRunId: string | null) {
  try {
    const statistics = await fetchFromApi<ReviewStatistics>("/api/v1/reviews/statistics");
    const selectedId = trainingRunId ?? chooseDefaultTrainingRun(statistics.per_training_run);
    if (!selectedId) {
      return { statistics, selectedId: null, performance: null, calibration: null, errors: null };
    }
    const query = `training_run_id=${selectedId}`;
    const [performance, calibration, errors] = await Promise.all([
      fetchFromApi<ProductionPerformance>(`/api/v1/reviews/performance?${query}`),
      fetchFromApi<CalibrationDiagnostics>(`/api/v1/reviews/calibration?${query}`),
      fetchFromApi<ErrorAnalysis>(`/api/v1/reviews/errors?${query}&error_type=false_positive&limit=8`),
    ]);
    const falseNegatives = await fetchFromApi<ErrorAnalysis>(`/api/v1/reviews/errors?${query}&error_type=false_negative&limit=8`);
    return {
      statistics,
      selectedId,
      performance,
      calibration,
      errors: { ...errors, items: [...errors.items, ...falseNegatives.items], total: errors.total + falseNegatives.total },
    };
  } catch {
    return null;
  }
}

function chooseDefaultTrainingRun(models: TrainingRunReviewSummary[]) {
  return (
    models.find((model) => model.is_champion)?.training_run_id ??
    models.find((model) => model.reviewed_count > 0)?.training_run_id ??
    models.find((model) => model.training_run_id)?.training_run_id ??
    null
  );
}

export default async function PerformancePage({ searchParams }: PerformancePageProps) {
  const params = (await searchParams) ?? {};
  const selectedParam = firstValue(params.training_run_id) ?? null;
  const data = await loadPerformance(selectedParam);

  return (
    <>
      <PageHeader
        eyebrow="Reviewed production metrics"
        title="Performance"
        description="Post-training evaluation from saved analyses with explicit human-verified labels. Held-out test metrics remain separate."
      />
      <div className="mx-auto grid w-full max-w-7xl gap-6 px-4 py-8 sm:px-6 lg:px-8">
        {!data ? (
          <section className="rounded-lg border border-amber-200 bg-amber-50 px-5 py-4 text-sm leading-6 text-amber-900">
            Backend review performance APIs are not reachable right now.
          </section>
        ) : data.statistics.reviewed_analyses === 0 ? (
          <EmptyState
            icon={UserCheck}
            title="Production performance cannot be measured yet"
            description="No saved analyses have human-verified labels. Review analyses to enable post-training performance metrics."
          />
        ) : data.performance && data.calibration && data.errors ? (
          <>
            <ModelSelector models={data.statistics.per_training_run} selectedId={data.selectedId} />
            <PreliminaryBanner performance={data.performance} />
            <MetricGrid performance={data.performance} />
            <div className="grid gap-6 lg:grid-cols-2">
              <ConfusionMatrixPanel performance={data.performance} />
              <TestComparison performance={data.performance} />
            </div>
            <div className="grid gap-6 lg:grid-cols-[1.1fr_0.9fr]">
              <ReliabilityPanel calibration={data.calibration} />
              <ErrorSummary errors={data.errors} />
            </div>
            <ErrorTable errors={data.errors} />
          </>
        ) : (
          <EmptyState
            icon={GitCompare}
            title="No eligible model selected"
            description="Saved analyses exist, but no model-scoped records are available for reviewed performance."
          />
        )}
      </div>
    </>
  );
}

function ModelSelector({ models, selectedId }: { models: TrainingRunReviewSummary[]; selectedId: string | null }) {
  return (
    <section className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
      <h2 className="text-sm font-semibold text-ink">Model selection</h2>
      <div className="mt-4 flex flex-wrap gap-2">
        {models.filter((model) => model.training_run_id).map((model) => (
          <Link
            key={model.training_run_id}
            href={`/performance?training_run_id=${model.training_run_id}`}
            className={
              model.training_run_id === selectedId
                ? "rounded-md bg-ink px-3 py-2 text-sm font-semibold text-white"
                : "rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold text-ink"
            }
          >
            {model.model_display_name} - {model.reviewed_count} reviewed
          </Link>
        ))}
      </div>
    </section>
  );
}

function PreliminaryBanner({ performance }: { performance: ProductionPerformance }) {
  if (performance.sufficiency_status === "sufficient") {
    return null;
  }
  return (
    <section className="rounded-lg border border-amber-200 bg-amber-50 px-5 py-4 text-sm leading-6 text-amber-900">
      Preliminary - small reviewed sample. {performance.reviewed_count} reviewed analyses are available; the configured minimum is {performance.minimum_reviewed_samples}.
    </section>
  );
}

function MetricGrid({ performance }: { performance: ProductionPerformance }) {
  return (
    <section className="grid gap-4 md:grid-cols-3 xl:grid-cols-6">
      <MetricCard label="Reviewed samples" value={String(performance.reviewed_count)} />
      <MetricCard label="Accuracy" value={formatMetric(performance.accuracy)} />
      <MetricCard label="Precision" value={formatMetric(performance.precision)} />
      <MetricCard label="Recall" value={formatMetric(performance.recall)} />
      <MetricCard label="F1" value={formatMetric(performance.f1)} />
      <MetricCard label="ROC-AUC" value={performance.roc_auc.available ? formatMetric(performance.roc_auc.value) : "N/A"} helper={performance.roc_auc.reason ?? undefined} />
    </section>
  );
}

function ConfusionMatrixPanel({ performance }: { performance: ProductionPerformance }) {
  const matrix = performance.confusion_matrix.matrix;
  return (
    <section className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
      <div className="flex items-center gap-2">
        <BarChart3 aria-hidden="true" className="h-4 w-4 text-signal" />
        <h2 className="text-lg font-semibold text-ink">Reviewed Analysis Confusion Matrix</h2>
      </div>
      <p className="mt-3 text-sm leading-6 text-slate-600">Rows are human-verified labels. Columns are model predictions. FAKE is the positive class.</p>
      <div className="mt-5 grid max-w-sm grid-cols-[90px_repeat(2,1fr)] gap-2 text-center text-sm">
        <span />
        <span className="font-semibold text-slate-600">Pred REAL</span>
        <span className="font-semibold text-slate-600">Pred FAKE</span>
        <span className="self-center font-semibold text-slate-600">Review REAL</span>
        <Cell value={matrix[0]?.[0] ?? 0} />
        <Cell value={matrix[0]?.[1] ?? 0} />
        <span className="self-center font-semibold text-slate-600">Review FAKE</span>
        <Cell value={matrix[1]?.[0] ?? 0} />
        <Cell value={matrix[1]?.[1] ?? 0} />
      </div>
    </section>
  );
}

function TestComparison({ performance }: { performance: ProductionPerformance }) {
  const test = performance.held_out_test_metrics;
  return (
    <section className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
      <div className="flex items-center gap-2">
        <GitCompare aria-hidden="true" className="h-4 w-4 text-signal" />
        <h2 className="text-lg font-semibold text-ink">Test vs Reviewed</h2>
      </div>
      <div className="mt-5 overflow-x-auto">
        <table className="min-w-full text-left text-sm">
          <thead className="text-xs uppercase tracking-wide text-slate-500">
            <tr>
              <th className="py-2 pr-4">Metric</th>
              <th className="py-2 pr-4">Held-out test</th>
              <th className="py-2 pr-4">Reviewed production-style</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {(["accuracy", "precision", "recall", "f1", "roc_auc"] as const).map((metric) => (
              <tr key={metric}>
                <td className="py-3 pr-4 font-medium text-ink">{metric.toUpperCase()}</td>
                <td className="py-3 pr-4 text-slate-700">{formatMetric(test?.[metric])}</td>
                <td className="py-3 pr-4 text-slate-700">{metric === "roc_auc" ? formatMetric(performance.roc_auc.value) : formatMetric(performance[metric])}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="mt-4 text-sm leading-6 text-slate-600">Differences are review signals, not automatic proof of drift or overfitting.</p>
    </section>
  );
}

function ReliabilityPanel({ calibration }: { calibration: CalibrationDiagnostics }) {
  const width = 420;
  const height = 260;
  const padding = 36;
  const plot = width - padding * 2;
  const points = calibration.reliability_bins.map((bin) => ({
    x: padding + bin.mean_confidence * plot,
    y: height - padding - bin.observed_accuracy * (height - padding * 2),
    label: `${Math.round(bin.lower_bound * 100)}-${Math.round(bin.upper_bound * 100)}%`,
    count: bin.sample_count,
  }));
  return (
    <section className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
      <div className="flex items-center gap-2">
        <Gauge aria-hidden="true" className="h-4 w-4 text-signal" />
        <h2 className="text-lg font-semibold text-ink">Reliability</h2>
      </div>
      <div className="mt-4 grid gap-3 text-sm text-slate-700 md:grid-cols-2">
        <p>Brier score: <span className="font-semibold text-ink">{formatMetric(calibration.brier_score)}</span></p>
        <p>ECE: <span className="font-semibold text-ink">{formatMetric(calibration.expected_calibration_error)}</span></p>
      </div>
      {points.length ? (
        <svg viewBox={`0 0 ${width} ${height}`} className="mt-5 h-auto w-full" role="img" aria-label="Reliability diagram">
          <line x1={padding} y1={height - padding} x2={width - padding} y2={padding} stroke="#94a3b8" strokeDasharray="4 4" />
          <line x1={padding} y1={height - padding} x2={width - padding} y2={height - padding} stroke="#334155" />
          <line x1={padding} y1={padding} x2={padding} y2={height - padding} stroke="#334155" />
          {points.map((point) => (
            <g key={point.label}>
              <circle cx={point.x} cy={point.y} r={Math.max(5, Math.min(14, point.count + 4))} fill="#0f766e" opacity="0.9" />
              <text x={point.x} y={point.y - 10} textAnchor="middle" className="fill-slate-600 text-[10px]">{point.count}</text>
            </g>
          ))}
          <text x={width / 2} y={height - 5} textAnchor="middle" className="fill-slate-600 text-xs">Mean confidence</text>
          <text x="14" y={height / 2} transform={`rotate(-90 14 ${height / 2})`} textAnchor="middle" className="fill-slate-600 text-xs">Observed accuracy</text>
        </svg>
      ) : (
        <p className="mt-4 text-sm leading-6 text-slate-600">Insufficient reviewed confidence data for calibration diagnostics.</p>
      )}
    </section>
  );
}

function ErrorSummary({ errors }: { errors: ErrorAnalysis }) {
  return (
    <section className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
      <div className="flex items-center gap-2">
        <AlertTriangle aria-hidden="true" className="h-4 w-4 text-signal" />
        <h2 className="text-lg font-semibold text-ink">High-Confidence Model Errors</h2>
      </div>
      <dl className="mt-5 grid grid-cols-2 gap-4 text-sm">
        <Definition label="High-conf errors" value={String(errors.statistics.high_confidence_error_count)} />
        <Definition
          label="High-conf error rate"
          value={formatPercentage(
            errors.statistics.high_confidence_error_rate === null
              ? null
              : errors.statistics.high_confidence_error_rate * 100
          )}
        />
        <Definition label="Avg confidence correct" value={formatMetric(errors.statistics.average_confidence_correct)} />
        <Definition label="Avg confidence incorrect" value={formatMetric(errors.statistics.average_confidence_incorrect)} />
      </dl>
      <p className="mt-4 text-sm leading-6 text-slate-600">{errors.definitions.false_positive}</p>
      <p className="mt-2 text-sm leading-6 text-slate-600">{errors.definitions.false_negative}</p>
    </section>
  );
}

function ErrorTable({ errors }: { errors: ErrorAnalysis }) {
  return (
    <section className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
      <h2 className="text-lg font-semibold text-ink">Reviewed error examples</h2>
      {errors.items.length ? (
        <div className="mt-5 overflow-x-auto">
          <table className="min-w-full divide-y divide-slate-200 text-left text-sm">
            <thead className="text-xs uppercase tracking-wide text-slate-500">
              <tr>
                <th className="px-3 py-3">Analysis</th>
                <th className="px-3 py-3">Prediction</th>
                <th className="px-3 py-3">Reviewed label</th>
                <th className="px-3 py-3">Confidence</th>
                <th className="px-3 py-3">Type</th>
                <th className="px-3 py-3">Date</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {errors.items.map((item) => (
                <tr key={`${item.error_type}-${item.analysis_id}`}>
                  <td className="px-3 py-4">
                    <Link href={`/history/${item.analysis_id}`} className="font-semibold text-ink">{item.title || "Untitled analysis"}</Link>
                    {item.article_preview ? <p className="mt-1 max-w-lg text-xs leading-5 text-slate-500">{item.article_preview}</p> : null}
                  </td>
                  <td className="px-3 py-4 text-slate-700">{item.predicted_label}</td>
                  <td className="px-3 py-4 text-slate-700">{item.verified_label}</td>
                  <td className="px-3 py-4 text-slate-700">{formatMetric(item.confidence)}</td>
                  <td className="px-3 py-4 text-slate-700">{item.error_type.replace("_", " ")}</td>
                  <td className="px-3 py-4 text-slate-700">{new Date(item.created_at).toLocaleDateString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <p className="mt-4 text-sm leading-6 text-slate-600">No reviewed false positives or false negatives for this model.</p>
      )}
    </section>
  );
}

function MetricCard({ label, value, helper }: { label: string; value: string; helper?: string }) {
  return (
    <div className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
      <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">{label}</p>
      <p className="mt-2 text-2xl font-semibold text-ink">{value}</p>
      {helper ? <p className="mt-1 text-xs leading-5 text-slate-500">{helper}</p> : null}
    </div>
  );
}

function Cell({ value }: { value: number }) {
  return <span className="rounded-md bg-surface px-4 py-3 text-lg font-semibold text-ink">{value}</span>;
}

function Definition({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <dt className="text-slate-500">{label}</dt>
      <dd className="mt-1 font-semibold text-ink">{value}</dd>
    </div>
  );
}
