import { Boxes, GitCompare } from "lucide-react";

import { EmptyState } from "@/components/EmptyState";
import { PageHeader } from "@/components/PageHeader";
import { TrainingAction } from "@/components/TrainingAction";
import {
  MLTrainingRun,
  PaginatedResponse,
  fetchFromApi,
  formatExplanationMethod,
  formatModelFamily,
  formatMetric,
  formatModelType,
} from "@/lib/api";

export const dynamic = "force-dynamic";

async function loadTrainingRuns() {
  try {
    return await fetchFromApi<PaginatedResponse<MLTrainingRun>>("/api/v1/ml/training-runs?limit=50&offset=0");
  } catch {
    return null;
  }
}

export default async function ModelsPage() {
  const trainingRuns = await loadTrainingRuns();
  const models = trainingRuns?.items ?? [];

  return (
    <>
      <PageHeader
        eyebrow="Model comparison"
        title="Models"
        description="A backend-driven registry for classical and transformer training runs, artifact availability, explainability support, and validation/test metrics."
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
                      <th className="px-3 py-3 font-semibold">Explainability</th>
                      <th className="px-3 py-3 font-semibold">Dataset size</th>
                      <th className="px-3 py-3 font-semibold">Text mode</th>
                      <th className="px-3 py-3 font-semibold">Validation F1</th>
                      <th className="px-3 py-3 font-semibold">Test F1</th>
                      <th className="px-3 py-3 font-semibold">Accuracy</th>
                      <th className="px-3 py-3 font-semibold">ROC-AUC</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {models.map((model) => (
                      <tr key={model.id}>
                        <td className="px-3 py-4">
                          <p className="font-medium text-ink">{model.model_display_name}</p>
                          <p className="text-xs text-slate-500">
                            {model.base_model_name ?? formatModelType(model.model_type)}
                          </p>
                        </td>
                        <td className="px-3 py-4 text-slate-700">{formatModelFamily(model.model_family)}</td>
                        <td className="px-3 py-4 text-slate-700">{model.status}</td>
                        <td className="px-3 py-4 text-slate-700">
                          <p>{model.explainability_supported ? "Supported" : "Not supported"}</p>
                          <p className="text-xs text-slate-500">{formatExplanationMethod(model.explanation_method)}</p>
                        </td>
                        <td className="px-3 py-4 text-slate-700">{model.dataset_article_count}</td>
                        <td className="px-3 py-4 text-slate-700">
                          {String(model.text_composition_config.mode ?? "N/A")}
                        </td>
                        <td className="px-3 py-4 text-slate-700">{formatMetric(model.validation_metrics?.f1)}</td>
                        <td className="px-3 py-4 text-slate-700">{formatMetric(model.test_metrics?.f1)}</td>
                        <td className="px-3 py-4 text-slate-700">{formatMetric(model.test_metrics?.accuracy)}</td>
                        <td className="px-3 py-4 text-slate-700">{formatMetric(model.test_metrics?.roc_auc)}</td>
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
