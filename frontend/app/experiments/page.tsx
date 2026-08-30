import Link from "next/link";
import { FlaskConical, Trophy } from "lucide-react";

import { EmptyState } from "@/components/EmptyState";
import { ExperimentComparisonClient } from "@/components/ExperimentComparisonClient";
import { PageHeader } from "@/components/PageHeader";
import {
  ChampionResponse,
  ExperimentSummary,
  PaginatedResponse,
  fetchFromApi,
  formatLifecycleStatus,
  formatMetric,
  formatModelFamily,
  formatModelType,
} from "@/lib/api";

export const dynamic = "force-dynamic";

async function loadExperiments() {
  try {
    const [experiments, champion] = await Promise.all([
      fetchFromApi<PaginatedResponse<ExperimentSummary>>("/api/v1/experiments?limit=50&offset=0"),
      fetchFromApi<ChampionResponse>("/api/v1/models/champion"),
    ]);
    return { experiments, champion };
  } catch {
    return null;
  }
}

export default async function ExperimentsPage() {
  const data = await loadExperiments();
  const experiments = data?.experiments.items ?? [];

  return (
    <>
      <PageHeader
        eyebrow="Experiment tracking"
        title="Experiments"
        description="Compare training runs, review lifecycle state, and manage the application's explicitly selected champion model."
      />
      <div className="mx-auto w-full max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
        {!data ? (
          <section className="mb-6 rounded-lg border border-amber-200 bg-amber-50 px-5 py-4 text-sm leading-6 text-amber-900">
            Backend experiment APIs are not reachable right now.
          </section>
        ) : null}
        {data && experiments.length === 0 ? (
          <EmptyState
            icon={FlaskConical}
            title="No experiments yet"
            description="Train models from imported datasets. Every training run becomes an experiment record."
          />
        ) : null}
        {data && experiments.length ? (
          <div className="grid gap-6">
            <section className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
              <div className="flex items-center gap-3">
                <span className="flex h-10 w-10 items-center justify-center rounded-lg bg-teal-50 text-signal">
                  <Trophy aria-hidden="true" className="h-5 w-5" />
                </span>
                <div>
                  <h2 className="text-lg font-semibold text-ink">Champion model</h2>
                  <p className="text-sm text-slate-500">
                    {data.champion.champion
                      ? `${data.champion.champion.model_display_name} is the current application default.`
                      : "No champion has been explicitly selected."}
                  </p>
                </div>
              </div>
            </section>

            <ExperimentComparisonClient experiments={experiments} />

            <section className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
              <div className="flex items-center gap-3">
                <span className="flex h-10 w-10 items-center justify-center rounded-lg bg-teal-50 text-signal">
                  <FlaskConical aria-hidden="true" className="h-5 w-5" />
                </span>
                <div>
                  <h2 className="text-lg font-semibold text-ink">Training-run experiments</h2>
                  <p className="text-sm text-slate-500">Stored metadata and held-out metrics from the model registry.</p>
                </div>
              </div>
              <div className="mt-5 overflow-x-auto">
                <table className="min-w-full divide-y divide-slate-200 text-left text-sm">
                  <thead>
                    <tr className="text-xs uppercase tracking-wide text-slate-500">
                      <th className="px-3 py-3 font-semibold">Run</th>
                      <th className="px-3 py-3 font-semibold">Family</th>
                      <th className="px-3 py-3 font-semibold">Execution</th>
                      <th className="px-3 py-3 font-semibold">Lifecycle</th>
                      <th className="px-3 py-3 font-semibold">Dataset</th>
                      <th className="px-3 py-3 font-semibold">Text mode</th>
                      <th className="px-3 py-3 font-semibold">Test F1</th>
                      <th className="px-3 py-3 font-semibold">Trained</th>
                      <th className="px-3 py-3 font-semibold">Detail</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {experiments.map((experiment) => (
                      <tr key={experiment.training_run_id}>
                        <td className="px-3 py-4">
                          <div className="flex flex-wrap items-center gap-2">
                            <p className="font-medium text-ink">{experiment.model_display_name}</p>
                            {experiment.is_champion ? (
                              <span className="rounded-md bg-amber-50 px-2 py-1 text-xs font-semibold text-amber-800">Champion</span>
                            ) : null}
                          </div>
                          <p className="text-xs text-slate-500">
                            {experiment.base_model_name ?? formatModelType(experiment.model_type)}
                          </p>
                        </td>
                        <td className="px-3 py-4 text-slate-700">{formatModelFamily(experiment.model_family)}</td>
                        <td className="px-3 py-4 text-slate-700">{experiment.execution_status}</td>
                        <td className="px-3 py-4 text-slate-700">{formatLifecycleStatus(experiment.lifecycle_status)}</td>
                        <td className="px-3 py-4 text-slate-700">{experiment.dataset_identifiers.join(", ") || "All imported"}</td>
                        <td className="px-3 py-4 text-slate-700">{experiment.text_composition_mode ?? "N/A"}</td>
                        <td className="px-3 py-4 text-slate-700">{formatMetric(experiment.primary_test_metric)}</td>
                        <td className="px-3 py-4 text-slate-700">
                          {experiment.trained_at ? new Date(experiment.trained_at).toLocaleString() : "N/A"}
                        </td>
                        <td className="px-3 py-4">
                          <Link
                            href={`/experiments/${experiment.training_run_id}`}
                            className="inline-flex items-center justify-center rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold text-ink"
                          >
                            View
                          </Link>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </section>
          </div>
        ) : null}
      </div>
    </>
  );
}
