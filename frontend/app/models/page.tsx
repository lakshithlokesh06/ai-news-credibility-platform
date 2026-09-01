import Link from "next/link";
import { Activity, Boxes, GitCompare } from "lucide-react";

import { EmptyState } from "@/components/EmptyState";
import { PageHeader } from "@/components/PageHeader";
import { TrainingAction } from "@/components/TrainingAction";
import {
  MLTrainingRun,
  PaginatedResponse,
  ReviewStatistics,
  fetchFromApi,
  formatExplanationMethod,
  formatLifecycleStatus,
  formatModelFamily,
  formatMetric,
  formatModelType,
  formatTrainingStatus,
} from "@/lib/api";

export const dynamic = "force-dynamic";

async function loadTrainingRuns() {
  try {
    const [trainingRuns, reviewStatistics] = await Promise.all([
      fetchFromApi<PaginatedResponse<MLTrainingRun>>("/api/v1/ml/training-runs?limit=50&offset=0"),
      fetchFromApi<ReviewStatistics>("/api/v1/reviews/statistics"),
    ]);
    return { trainingRuns, reviewStatistics };
  } catch {
    return null;
  }
}

export default async function ModelsPage() {
  const trainingRuns = await loadTrainingRuns();
  const models = trainingRuns?.trainingRuns.items ?? [];
  const reviewCounts = new Map(
    (trainingRuns?.reviewStatistics.per_training_run ?? []).map((item) => [item.training_run_id, item.reviewed_count])
  );

  return (
    <>
      <PageHeader
        eyebrow="Model comparison"
        title="Models"
        description="A backend-driven registry for classical and transformer training runs, lifecycle state, artifact availability, explainability support, and held-out test metrics."
      />
      <div className="mx-auto w-full max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
        <div className="grid gap-6">
          <TrainingAction />
          {!trainingRuns ? (
            <section className="rounded-lg border border-amber-200 bg-amber-50 px-5 py-4 text-sm leading-6 text-amber-900">
              Backend model registry APIs are not reachable right now.
            </section>
          ) : null}
          {models.length ? (
            <section className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
              <div className="flex items-center gap-3">
                <span className="flex h-10 w-10 items-center justify-center rounded-lg bg-teal-50 text-signal">
                  <Boxes aria-hidden="true" className="h-5 w-5" />
                </span>
                <div>
                  <h2 className="text-lg font-semibold text-ink">Model registry</h2>
                  <p className="text-sm text-slate-500">Real training-run metadata from the backend.</p>
                </div>
              </div>
              <div className="mt-5 overflow-x-auto">
                <table className="min-w-full divide-y divide-slate-200 text-left text-sm">
                  <thead>
                    <tr className="text-xs uppercase tracking-wide text-slate-500">
                      <th className="px-3 py-3 font-semibold">Model</th>
                      <th className="px-3 py-3 font-semibold">Family</th>
                      <th className="px-3 py-3 font-semibold">Status</th>
                      <th className="px-3 py-3 font-semibold">Lifecycle</th>
                      <th className="px-3 py-3 font-semibold">Explainability</th>
                      <th className="px-3 py-3 font-semibold">Test F1</th>
                      <th className="px-3 py-3 font-semibold">Training date</th>
                      <th className="px-3 py-3 font-semibold">ROC-AUC</th>
                      <th className="px-3 py-3 font-semibold">Reviewed</th>
                      <th className="px-3 py-3 font-semibold">Monitoring</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {models.map((model) => (
                      <tr key={model.id}>
                        <td className="px-3 py-4">
                          <p className="font-medium text-ink">{model.model_display_name}</p>
                          {model.lifecycle_status === "champion" ? (
                            <span className="mt-2 inline-flex rounded-md bg-amber-50 px-2 py-1 text-xs font-semibold text-amber-800">
                              Champion
                            </span>
                          ) : null}
                          <p className="text-xs text-slate-500">
                            {model.base_model_name ?? formatModelType(model.model_type)}
                          </p>
                        </td>
                        <td className="px-3 py-4 text-slate-700">{formatModelFamily(model.model_family)}</td>
                        <td className="px-3 py-4 text-slate-700">{formatTrainingStatus(model.status)}</td>
                        <td className="px-3 py-4 text-slate-700">{formatLifecycleStatus(model.lifecycle_status)}</td>
                        <td className="px-3 py-4 text-slate-700">
                          <p>{model.explainability_supported ? "Supported" : "Not supported"}</p>
                          <p className="text-xs text-slate-500">{formatExplanationMethod(model.explanation_method)}</p>
                        </td>
                        <td className="px-3 py-4 text-slate-700">
                          {formatMetric(model.test_metrics?.f1)}
                        </td>
                        <td className="px-3 py-4 text-slate-700">
                          {model.completed_at ? new Date(model.completed_at).toLocaleDateString() : "N/A"}
                        </td>
                        <td className="px-3 py-4 text-slate-700">{formatMetric(model.test_metrics?.roc_auc)}</td>
                        <td className="px-3 py-4 text-slate-700">
                          {model.status === "completed" ? (
                            <Link href={`/performance?training_run_id=${model.id}`} className="font-semibold text-ink">
                              {reviewCounts.get(model.id) ?? 0} samples
                            </Link>
                          ) : (
                            <span className="text-xs text-slate-500">N/A</span>
                          )}
                        </td>
                        <td className="px-3 py-4">
                          {model.status === "completed" ? (
                            <div className="flex flex-wrap gap-2">
                              <Link
                                href={`/monitoring/${model.id}`}
                                className="inline-flex items-center gap-2 rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold text-ink"
                              >
                                <Activity aria-hidden="true" className="h-4 w-4" />
                                View
                              </Link>
                              <Link
                                href={`/experiments/${model.id}`}
                                className="inline-flex items-center rounded-md border border-slate-300 px-3 py-2 text-sm font-semibold text-ink"
                              >
                                Experiment
                              </Link>
                            </div>
                          ) : (
                            <span className="text-xs text-slate-500">Available after completion</span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </section>
          ) : (
            <EmptyState
              icon={GitCompare}
              title="No models registered yet"
              description="Train a baseline after importing a labeled dataset. The registry will stay empty until real training runs exist."
            />
          )}
        </div>
      </div>
    </>
  );
}
