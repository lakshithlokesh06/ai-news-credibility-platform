import Link from "next/link";
import { Activity, AlertTriangle, BarChart3, Gauge, ShieldCheck } from "lucide-react";

import { EmptyState } from "@/components/EmptyState";
import { PageHeader } from "@/components/PageHeader";
import {
  MonitoringOverview,
  MonitoringOverviewItem,
  fetchFromApi,
  formatMetric,
  formatModelFamily,
  formatModelType,
  formatMonitoringStatus,
} from "@/lib/api";

export const dynamic = "force-dynamic";

async function loadMonitoringOverview() {
  try {
    return await fetchFromApi<MonitoringOverview>("/api/v1/monitoring");
  } catch {
    return null;
  }
}

export default async function MonitoringPage() {
  const overview = await loadMonitoringOverview();
  const items = overview?.items ?? [];

  return (
    <>
      <PageHeader
        eyebrow="Model reliability"
        title="Monitoring"
        description="Track per-model usage, confidence, prediction-distribution shift, and input drift from saved analysis history."
      />
      <div className="mx-auto w-full max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
        {!overview ? (
          <section className="mb-6 rounded-lg border border-amber-200 bg-amber-50 px-5 py-4 text-sm leading-6 text-amber-900">
            Backend monitoring APIs are not reachable right now.
          </section>
        ) : null}
        {overview && items.length === 0 ? (
          <EmptyState
            icon={Activity}
            title="No completed models to monitor"
            description="Train a model and save analyses from the analysis workspace. Monitoring begins from stored model outputs and reference profiles."
          />
        ) : null}
        {overview && items.length ? (
          <div className="grid gap-6">
            <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-5">
              <MetricCard icon={ShieldCheck} label="Completed models" value={String(overview.total_completed_models)} />
              <MetricCard icon={Gauge} label="Healthy" value={String(overview.healthy_models)} />
              <MetricCard icon={AlertTriangle} label="Needs attention" value={String(overview.models_needing_attention)} />
              <MetricCard icon={BarChart3} label="Insufficient data" value={String(overview.insufficient_data_models)} />
              <MetricCard icon={Activity} label="Recent analyses" value={String(overview.recent_analyses)} />
            </section>

            <section className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
              <div className="flex items-center gap-3">
                <span className="flex h-10 w-10 items-center justify-center rounded-lg bg-teal-50 text-signal">
                  <Activity aria-hidden="true" className="h-5 w-5" />
                </span>
                <div>
                  <h2 className="text-lg font-semibold text-ink">Model monitoring status</h2>
                  <p className="text-sm text-slate-500">Latest saved analysis window, scoped to each training run.</p>
                </div>
              </div>
              <div className="mt-5 overflow-x-auto">
                <table className="min-w-full divide-y divide-slate-200 text-left text-sm">
                  <thead>
                    <tr className="text-xs uppercase tracking-wide text-slate-500">
                      <th className="px-3 py-3 font-semibold">Model</th>
                      <th className="px-3 py-3 font-semibold">Status</th>
                      <th className="px-3 py-3 font-semibold">Input drift</th>
                      <th className="px-3 py-3 font-semibold">Prediction drift</th>
                      <th className="px-3 py-3 font-semibold">Window analyses</th>
                      <th className="px-3 py-3 font-semibold">Average confidence</th>
                      <th className="px-3 py-3 font-semibold">Last analyzed</th>
                      <th className="px-3 py-3 font-semibold">Detail</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {items.map((item) => (
                      <MonitoringRow key={item.training_run_id} item={item} />
                    ))}
                  </tbody>
                </table>
              </div>
            </section>

            <section className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
              <h2 className="text-sm font-semibold text-ink">Monitoring boundary</h2>
              <ul className="mt-3 grid gap-2 text-sm leading-6 text-slate-600 md:grid-cols-2">
                {overview.limitations.map((limitation) => (
                  <li key={limitation}>{limitation}</li>
                ))}
              </ul>
            </section>
          </div>
        ) : null}
      </div>
    </>
  );
}

function MonitoringRow({ item }: { item: MonitoringOverviewItem }) {
  return (
    <tr>
      <td className="px-3 py-4">
        <p className="font-medium text-ink">{item.model_display_name}</p>
        <p className="text-xs text-slate-500">
          {formatModelFamily(item.model_family)} / {item.model_name ?? formatModelType(item.model_type)}
        </p>
      </td>
      <td className="px-3 py-4">
        <StatusBadge status={item.monitoring_status} />
      </td>
      <td className="px-3 py-4">
        <StatusBadge status={item.input_drift_status} />
      </td>
      <td className="px-3 py-4">
        <StatusBadge status={item.prediction_drift_status} />
      </td>
      <td className="px-3 py-4 text-slate-700">{item.recent_analysis_count}</td>
      <td className="px-3 py-4 text-slate-700">{formatMetric(item.average_confidence)}</td>
      <td className="px-3 py-4 text-slate-700">
        {item.last_analyzed_at ? new Date(item.last_analyzed_at).toLocaleString() : "N/A"}
      </td>
      <td className="px-3 py-4">
        <Link
          href={`/monitoring/${item.training_run_id}`}
          className="inline-flex items-center justify-center rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold text-ink"
        >
          View
        </Link>
      </td>
    </tr>
  );
}

function MetricCard({
  icon: Icon,
  label,
  value,
}: {
  icon: typeof Activity;
  label: string;
  value: string;
}) {
  return (
    <div className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex items-center gap-2">
        <Icon aria-hidden="true" className="h-4 w-4 text-signal" />
        <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">{label}</p>
      </div>
      <p className="mt-2 text-2xl font-semibold text-ink">{value}</p>
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
