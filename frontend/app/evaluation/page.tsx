import { BarChart3, Scale } from "lucide-react";

import { EmptyState } from "@/components/EmptyState";
import { PageHeader } from "@/components/PageHeader";
import {
  ModelComparison,
  fetchFromApi,
  formatModelFamily,
  formatMetric,
  formatModelType,
} from "@/lib/api";

export const dynamic = "force-dynamic";

async function loadComparison() {
  try {
    return await fetchFromApi<ModelComparison>("/api/v1/ml/model-comparison?metric_source=test&primary_metric=f1");
  } catch {
    return null;
  }
}

export default async function EvaluationPage() {
  const comparison = await loadComparison();
  const completedModels = comparison?.items ?? [];

  return (
    <>
      <PageHeader
        eyebrow="Evaluation dashboard"
        title="Evaluation"
        description="Compare completed runs using stored validation and untouched test metrics. Production usage and drift diagnostics live in Monitoring."
      />
      <div className="mx-auto w-full max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
        {!comparison ? (
          <section className="mb-6 rounded-lg border border-amber-200 bg-amber-50 px-5 py-4 text-sm leading-6 text-amber-900">
            Backend evaluation APIs are not reachable right now.
          </section>
        ) : null}
        {completedModels.length ? (
          <div className="grid gap-6">
            <section className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
              <div className="flex items-center gap-3">
                <span className="flex h-10 w-10 items-center justify-center rounded-lg bg-teal-50 text-signal">
                  <Scale aria-hidden="true" className="h-5 w-5" />
                </span>
                <div>
                  <h2 className="text-lg font-semibold text-ink">Model comparison</h2>
                  <p className="text-sm text-slate-500">
                    Primary criterion: {comparison?.metric_source} {comparison?.primary_metric}
                  </p>
                </div>
              </div>
              <div className="mt-5 grid gap-4 md:grid-cols-2">
                {completedModels.map((item) => (
                  <article key={item.training_run_id} className="rounded-lg border border-slate-200 bg-surface p-5">
                    <div className="flex items-start justify-between gap-4">
                      <div>
                        <h3 className="font-semibold text-ink">{item.model_display_name}</h3>
                        <p className="mt-1 text-sm text-slate-500">
                          {formatModelFamily(item.model_family)} /{" "}
                          {item.base_model_name ?? formatModelType(item.model_type)}
                        </p>
                      </div>
                      {comparison?.recommended_training_run_id === item.training_run_id ? (
                        <span className="rounded-md bg-teal-50 px-2 py-1 text-xs font-semibold text-signal">
                          Top by test F1
                        </span>
                      ) : null}
                    </div>
                    <dl className="mt-5 grid grid-cols-2 gap-3 text-sm">
                      <div>
                        <dt className="text-slate-500">Test accuracy</dt>
                        <dd className="mt-1 font-semibold text-ink">{formatMetric(item.test_metrics?.accuracy)}</dd>
                      </div>
                      <div>
                        <dt className="text-slate-500">Test F1</dt>
                        <dd className="mt-1 font-semibold text-ink">{formatMetric(item.test_metrics?.f1)}</dd>
                      </div>
                      <div>
                        <dt className="text-slate-500">Precision</dt>
                        <dd className="mt-1 font-semibold text-ink">{formatMetric(item.test_metrics?.precision)}</dd>
                      </div>
                      <div>
                        <dt className="text-slate-500">Recall</dt>
                        <dd className="mt-1 font-semibold text-ink">{formatMetric(item.test_metrics?.recall)}</dd>
                      </div>
                      <div>
                        <dt className="text-slate-500">ROC-AUC</dt>
                        <dd className="mt-1 font-semibold text-ink">{formatMetric(item.test_metrics?.roc_auc)}</dd>
                      </div>
                      <div>
                        <dt className="text-slate-500">Validation F1</dt>
                        <dd className="mt-1 font-semibold text-ink">{formatMetric(item.validation_metrics?.f1)}</dd>
                      </div>
                    </dl>
                    {item.test_metrics?.confusion_matrix ? (
                      <div className="mt-5">
                        <p className="text-sm font-medium text-slate-700">Test confusion matrix</p>
                        <div className="mt-2 grid w-48 grid-cols-2 gap-2 text-center text-sm font-semibold">
                          {item.test_metrics.confusion_matrix.flat().map((value, index) => (
                            <span key={`${item.training_run_id}-${index}`} className="rounded-md bg-white px-3 py-2 text-ink">
                              {value}
                            </span>
                          ))}
                        </div>
                        <p className="mt-2 text-xs text-slate-500">Rows: actual REAL/FAKE. Columns: predicted REAL/FAKE.</p>
                      </div>
                    ) : null}
                  </article>
                ))}
              </div>
            </section>
          </div>
        ) : (
          <EmptyState
            icon={BarChart3}
            title="Evaluation runs will appear here"
            description="No synthetic metrics are shown. Train completed models from imported datasets to populate this page."
          />
        )}
      </div>
    </>
  );
}
