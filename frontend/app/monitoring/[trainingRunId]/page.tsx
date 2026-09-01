import Link from "next/link";
import { ArrowLeft, Activity, BarChart3, Database, Gauge, RefreshCw } from "lucide-react";

import { EmptyState } from "@/components/EmptyState";
import { PageHeader } from "@/components/PageHeader";
import { RefreshMonitoringProfileButton } from "@/components/RefreshMonitoringProfileButton";
import {
  ModelMonitoring,
  MonitoringMetric,
  ReviewStatistics,
  fetchFromApi,
  formatMetric,
  formatModelFamily,
  formatModelType,
  formatMonitoringStatus,
  formatPercentage,
} from "@/lib/api";

export const dynamic = "force-dynamic";

type MonitoringDetailPageProps = {
  params: Promise<{ trainingRunId: string }>;
};

async function loadMonitoring(trainingRunId: string) {
  try {
    const [monitoring, reviewStatistics] = await Promise.all([
      fetchFromApi<ModelMonitoring>(`/api/v1/monitoring/models/${trainingRunId}`),
      fetchFromApi<ReviewStatistics>("/api/v1/reviews/statistics"),
    ]);
    return { monitoring, reviewStatistics };
  } catch {
    return null;
  }
}

export default async function MonitoringDetailPage({ params }: MonitoringDetailPageProps) {
  const { trainingRunId } = await params;
  const data = await loadMonitoring(trainingRunId);

  if (!data) {
    return (
      <>
        <PageHeader
          eyebrow="Model monitoring"
          title="Monitoring detail"
          description="This training run could not be monitored."
        />
        <div className="mx-auto w-full max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
          <EmptyState
            icon={Activity}
            title="Monitoring detail unavailable"
            description="The training run may be missing, incomplete, or the monitoring API may be unavailable."
          />
        </div>
      </>
    );
  }

  const monitoring = data.monitoring;
  const reviewedCount =
    data.reviewStatistics.per_training_run.find((item) => item.training_run_id === monitoring.training_run_id)?.reviewed_count ?? 0;
  const referenceStats = monitoring.reference_profile?.reference_statistics ?? {};
  const textLengthStats = asRecord(referenceStats.text_length);
  const titleLengthStats = asRecord(referenceStats.title_length);

  return (
    <>
      <PageHeader
        eyebrow="Model monitoring"
        title={monitoring.model_display_name}
        description="Per-training-run behavior diagnostics from saved prediction history and a stored training-reference profile. Reviewed labels are required to measure production accuracy."
      />
      <div className="mx-auto grid w-full max-w-7xl gap-6 px-4 py-8 sm:px-6 lg:grid-cols-[1fr_340px] lg:px-8">
        <section className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
          <Link href="/monitoring" className="inline-flex items-center gap-2 text-sm font-semibold text-ink">
            <ArrowLeft aria-hidden="true" className="h-4 w-4" />
            Back to monitoring
          </Link>
          <div className="mt-6 flex flex-wrap items-center gap-3">
            <StatusBadge status={monitoring.overall_status} />
            <span className="rounded-md bg-slate-100 px-2 py-1 text-xs font-medium text-slate-600">
              {formatModelFamily(monitoring.model_family)} / {monitoring.model_name ?? formatModelType(monitoring.model_type)}
            </span>
            <span className="rounded-md bg-slate-100 px-2 py-1 text-xs font-medium text-slate-600">
              Window {monitoring.monitoring_window.window_size ?? "N/A"}
            </span>
          </div>
          <div className="mt-6 grid gap-4 md:grid-cols-4">
            <MetricCard label="Window analyses" value={String(monitoring.usage_metrics.analyses_in_window)} />
            <MetricCard label="Total analyses" value={String(monitoring.usage_metrics.total_analyses)} />
            <MetricCard label="Average confidence" value={formatMetric(monitoring.usage_metrics.average_confidence)} />
            <MetricCard label="Reference samples" value={String(monitoring.sample_counts.reference ?? 0)} />
          </div>
          {monitoring.status_reasons.length ? (
            <div className="mt-6 rounded-md bg-slate-50 px-4 py-3 text-sm leading-6 text-slate-600">
              {monitoring.status_reasons.map((reason) => (
                <p key={reason}>{reason}</p>
              ))}
            </div>
          ) : null}
        </section>

        <aside className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
          <div className="flex items-center gap-2">
            <Database aria-hidden="true" className="h-4 w-4 text-signal" />
            <h2 className="text-lg font-semibold text-ink">Reference profile</h2>
          </div>
          <div className="mt-5 grid gap-3 text-sm text-slate-700">
            <p>Status: {monitoring.reference_profile_status}</p>
            <p>Version: {monitoring.reference_profile?.profile_version ?? "N/A"}</p>
            <p>Created: {monitoring.reference_profile ? new Date(monitoring.reference_profile.created_at).toLocaleString() : "N/A"}</p>
            <p>REAL reference: {monitoring.reference_profile?.reference_label_distribution.REAL ?? 0}</p>
            <p>FAKE reference: {monitoring.reference_profile?.reference_label_distribution.FAKE ?? 0}</p>
            <p>Avg text length: {formatMetric(asNumber(textLengthStats.average))}</p>
            <p>Avg title length: {formatMetric(asNumber(titleLengthStats.average))}</p>
          </div>
          <div className="mt-6 border-t border-slate-200 pt-5">
            <RefreshMonitoringProfileButton trainingRunId={monitoring.training_run_id} />
          </div>
          {reviewedCount > 0 ? (
            <div className="mt-5 rounded-md bg-teal-50 px-4 py-3 text-sm leading-6 text-teal-900">
              <p className="font-semibold">Reviewed production performance available</p>
              <p>{reviewedCount} human-reviewed samples.</p>
              <Link href={`/performance?training_run_id=${monitoring.training_run_id}`} className="font-semibold text-ink">
                View performance
              </Link>
            </div>
          ) : null}
        </aside>

        <section className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm lg:col-span-2">
          <div className="flex items-center gap-2">
            <BarChart3 aria-hidden="true" className="h-4 w-4 text-signal" />
            <h2 className="text-lg font-semibold text-ink">Drift diagnostics</h2>
          </div>
          <div className="mt-5 grid gap-4 lg:grid-cols-2">
            <MetricPanel title="Prediction distribution" metric={monitoring.prediction_drift} />
            <MetricPanel title="Confidence shift" metric={monitoring.confidence_metrics.confidence_shift} />
            {monitoring.input_drift_metrics.map((metric) => (
              <MetricPanel key={metric.metric_name} title={formatMetricName(metric.metric_name)} metric={metric} />
            ))}
          </div>
        </section>

        <section className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
          <div className="flex items-center gap-2">
            <Gauge aria-hidden="true" className="h-4 w-4 text-signal" />
            <h2 className="text-lg font-semibold text-ink">Confidence</h2>
          </div>
          <dl className="mt-5 grid grid-cols-2 gap-4 text-sm">
            <MetricDefinition label="Average" value={formatMetric(monitoring.confidence_metrics.average_confidence)} />
            <MetricDefinition label="Median" value={formatMetric(monitoring.confidence_metrics.median_confidence)} />
            <MetricDefinition label="Low confidence" value={formatPercentage(monitoring.confidence_metrics.low_confidence_rate)} />
            <MetricDefinition label="High confidence" value={formatPercentage(monitoring.confidence_metrics.high_confidence_rate)} />
            <MetricDefinition label="Avg REAL prob." value={formatMetric(monitoring.confidence_metrics.average_real_probability)} />
            <MetricDefinition label="Avg FAKE prob." value={formatMetric(monitoring.confidence_metrics.average_fake_probability)} />
          </dl>
          <Histogram values={monitoring.confidence_metrics.confidence_distribution} labels={["<0.60", "0.60s", "0.70s", "0.80s", "0.90+"]} />
        </section>

        <section className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
          <div className="flex items-center gap-2">
            <Activity aria-hidden="true" className="h-4 w-4 text-signal" />
            <h2 className="text-lg font-semibold text-ink">Usage</h2>
          </div>
          <dl className="mt-5 grid grid-cols-2 gap-4 text-sm">
            <MetricDefinition label="Likely credible" value={String(monitoring.usage_metrics.real_prediction_count)} />
            <MetricDefinition label="Likely misinformation" value={String(monitoring.usage_metrics.fake_prediction_count)} />
            <MetricDefinition label="Explanations" value={formatPercentage(monitoring.usage_metrics.explanation_generation_rate)} />
            <MetricDefinition label="Last used" value={monitoring.usage_metrics.last_used_at ? new Date(monitoring.usage_metrics.last_used_at).toLocaleString() : "N/A"} />
          </dl>
          <div className="mt-5 grid gap-2">
            {monitoring.usage_metrics.recent_volume.slice(-7).map((item) => {
              const max = Math.max(...monitoring.usage_metrics.recent_volume.map((volume) => volume.count), 1);
              return (
                <div key={item.date} className="grid gap-1">
                  <div className="flex justify-between text-xs text-slate-500">
                    <span>{item.date}</span>
                    <span>{item.count}</span>
                  </div>
                  <div className="h-2 rounded-full bg-slate-100">
                    <div className="h-2 rounded-full bg-signal" style={{ width: `${Math.max(8, (item.count / max) * 100)}%` }} />
                  </div>
                </div>
              );
            })}
          </div>
        </section>

        <section className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm lg:col-span-2">
          <div className="flex items-center gap-2">
            <RefreshCw aria-hidden="true" className="h-4 w-4 text-signal" />
            <h2 className="text-sm font-semibold text-ink">Operational boundary</h2>
          </div>
          <ul className="mt-3 grid gap-2 text-sm leading-6 text-slate-600 md:grid-cols-2">
            {monitoring.limitations.map((limitation) => (
              <li key={limitation}>{limitation}</li>
            ))}
          </ul>
        </section>
      </div>
    </>
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

function MetricPanel({ title, metric }: { title: string; metric: MonitoringMetric }) {
  return (
    <article className="rounded-lg border border-slate-200 bg-surface p-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h3 className="text-sm font-semibold text-ink">{title}</h3>
        <StatusBadge status={metric.status} />
      </div>
      <p className="mt-3 text-2xl font-semibold text-ink">{formatMetric(metric.metric_value)}</p>
      <p className="mt-2 text-sm leading-6 text-slate-600">{metric.interpretation}</p>
      <p className="mt-3 text-xs text-slate-500">
        Warning {formatMetric(metric.warning_threshold)} / drift {formatMetric(metric.drift_threshold)}
      </p>
    </article>
  );
}

function MetricDefinition({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <dt className="text-slate-500">{label}</dt>
      <dd className="mt-1 font-semibold text-ink">{value}</dd>
    </div>
  );
}

function Histogram({ values, labels }: { values: number[]; labels: string[] }) {
  const max = Math.max(...values, 1);
  return (
    <div className="mt-6 grid gap-2">
      {values.map((value, index) => (
        <div key={`${labels[index]}-${index}`} className="grid gap-1">
          <div className="flex justify-between text-xs text-slate-500">
            <span>{labels[index]}</span>
            <span>{value}</span>
          </div>
          <div className="h-2 rounded-full bg-slate-100">
            <div className="h-2 rounded-full bg-ink" style={{ width: `${Math.max(value === 0 ? 0 : 8, (value / max) * 100)}%` }} />
          </div>
        </div>
      ))}
    </div>
  );
}

function StatusBadge({ status }: { status: string }) {
  const classes: Record<string, string> = {
    healthy: "bg-emerald-50 text-emerald-800",
    stable: "bg-emerald-50 text-emerald-800",
    watch: "bg-amber-50 text-amber-800",
    warning: "bg-amber-50 text-amber-800",
    drift_detected: "bg-rose-50 text-rose-800",
    insufficient_data: "bg-slate-100 text-slate-600",
  };
  return (
    <span className={`rounded-md px-2 py-1 text-xs font-semibold ${classes[status] ?? "bg-slate-100 text-slate-600"}`}>
      {formatMonitoringStatus(status)}
    </span>
  );
}

function formatMetricName(value: string) {
  const labels: Record<string, string> = {
    text_length_psi: "Text length PSI",
    title_length_psi: "Title length PSI",
    text_length_ks_statistic: "Text length KS",
  };
  return labels[value] ?? value;
}

function asRecord(value: unknown): Record<string, unknown> {
  return typeof value === "object" && value !== null ? (value as Record<string, unknown>) : {};
}

function asNumber(value: unknown): number | null {
  return typeof value === "number" ? value : null;
}
