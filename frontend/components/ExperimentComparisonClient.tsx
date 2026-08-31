"use client";

import { GitCompare, Loader2 } from "lucide-react";
import { useMemo, useState } from "react";

import {
  ExperimentComparison,
  ExperimentSummary,
  apiBaseUrl,
  apiErrorMessage,
  formatMetric,
  formatModelFamily,
  formatModelType,
} from "@/lib/api";

type ExperimentComparisonClientProps = {
  experiments: ExperimentSummary[];
};

const metricOptions = ["f1", "accuracy", "precision", "recall", "roc_auc"] as const;
const sourceOptions = ["test", "validation"] as const;

export function ExperimentComparisonClient({ experiments }: ExperimentComparisonClientProps) {
  const comparableCandidates = experiments.filter((item) => item.execution_status === "completed");
  const [selectedIds, setSelectedIds] = useState<string[]>(comparableCandidates.slice(0, 2).map((item) => item.training_run_id));
  const [primaryMetric, setPrimaryMetric] = useState<(typeof metricOptions)[number]>("f1");
  const [metricSource, setMetricSource] = useState<(typeof sourceOptions)[number]>("test");
  const [comparison, setComparison] = useState<ExperimentComparison | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const selectedCount = selectedIds.length;
  const maxValue = useMemo(
    () => Math.max(...(comparison?.items.map((item) => item.primary_metric_value ?? Number.NEGATIVE_INFINITY) ?? [])),
    [comparison],
  );

  function toggleSelection(trainingRunId: string) {
    setComparison(null);
    setError(null);
    setSelectedIds((current) => {
      if (current.includes(trainingRunId)) {
        return current.filter((id) => id !== trainingRunId);
      }
      if (current.length >= 4) {
        return current;
      }
      return [...current, trainingRunId];
    });
  }

  async function compare() {
    setError(null);
    setComparison(null);
    if (selectedCount < 2) {
      setError("Select 2 to 4 completed experiments.");
      return;
    }
    setIsLoading(true);
    try {
      const response = await fetch(`${apiBaseUrl}/api/v1/experiments/compare`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          training_run_ids: selectedIds,
          primary_metric: primaryMetric,
          metric_source: metricSource,
        }),
      });
      const payload = await response.json();
      if (!response.ok) {
        setError(apiErrorMessage(payload, "Comparison failed."));
        return;
      }
      setComparison(payload as ExperimentComparison);
    } catch {
      setError("Backend experiment comparison API is not reachable.");
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <section className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div className="flex items-center gap-3">
          <span className="flex h-10 w-10 items-center justify-center rounded-lg bg-teal-50 text-signal">
            <GitCompare aria-hidden="true" className="h-5 w-5" />
          </span>
          <div>
            <h2 className="text-lg font-semibold text-ink">Compare experiments</h2>
            <p className="text-sm text-slate-500">Select 2 to 4 completed runs and rank by one persisted metric.</p>
          </div>
        </div>
        <div className="grid gap-3 sm:grid-cols-[150px_150px_auto]">
          <select
            value={metricSource}
            onChange={(event) => setMetricSource(event.target.value as (typeof sourceOptions)[number])}
            className="h-10 rounded-md border border-slate-300 bg-white px-3 text-sm text-slate-700"
          >
            {sourceOptions.map((option) => (
              <option key={option} value={option}>{option}</option>
            ))}
          </select>
          <select
            value={primaryMetric}
            onChange={(event) => setPrimaryMetric(event.target.value as (typeof metricOptions)[number])}
            className="h-10 rounded-md border border-slate-300 bg-white px-3 text-sm text-slate-700"
          >
            {metricOptions.map((option) => (
              <option key={option} value={option}>{option}</option>
            ))}
          </select>
          <button
            type="button"
            onClick={compare}
            disabled={isLoading}
            className="inline-flex h-10 items-center justify-center gap-2 rounded-md bg-ink px-4 text-sm font-semibold text-white disabled:bg-slate-300"
          >
            {isLoading ? <Loader2 aria-hidden="true" className="h-4 w-4 animate-spin" /> : <GitCompare aria-hidden="true" className="h-4 w-4" />}
            Compare
          </button>
        </div>
      </div>

      <div className="mt-5 grid gap-3 md:grid-cols-2 xl:grid-cols-4">
        {comparableCandidates.map((experiment) => (
          <label key={experiment.training_run_id} className="rounded-lg border border-slate-200 bg-surface p-4">
            <div className="flex items-start gap-3">
              <input
                type="checkbox"
                checked={selectedIds.includes(experiment.training_run_id)}
                onChange={() => toggleSelection(experiment.training_run_id)}
                className="mt-1 h-4 w-4 rounded border-slate-300"
              />
              <div>
                <p className="font-semibold text-ink">{experiment.model_display_name}</p>
                <p className="mt-1 text-xs text-slate-500">
                  {formatModelFamily(experiment.model_family)} / {experiment.base_model_name ?? formatModelType(experiment.model_type)}
                </p>
                <p className="mt-2 text-xs text-slate-500">
                  Test F1 {formatMetric(experiment.primary_test_metric)}
                  {experiment.is_champion ? " / Champion" : ""}
                </p>
              </div>
            </div>
          </label>
        ))}
      </div>

      {error ? <p className="mt-4 rounded-md bg-amber-50 px-4 py-3 text-sm leading-6 text-amber-900">{error}</p> : null}

      {comparison ? (
        <div className="mt-6 grid gap-4">
          {comparison.comparability_status !== "directly_comparable" ? (
            <div className="rounded-md border border-amber-200 bg-amber-50 px-4 py-3 text-sm leading-6 text-amber-900">
              <p>These experiments have limited comparability. Metric ranking may not represent a fair head-to-head comparison.</p>
              {comparison.comparability_warnings.map((warning) => (
                <p key={warning}>{warning}</p>
              ))}
            </div>
          ) : null}
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-slate-200 text-left text-sm">
              <thead>
                <tr className="text-xs uppercase tracking-wide text-slate-500">
                  <th className="px-3 py-3 font-semibold">Model</th>
                  <th className="px-3 py-3 font-semibold">Family</th>
                  <th className="px-3 py-3 font-semibold">Dataset</th>
                  <th className="px-3 py-3 font-semibold">Text mode</th>
                  <th className="px-3 py-3 font-semibold">Accuracy</th>
                  <th className="px-3 py-3 font-semibold">Precision</th>
                  <th className="px-3 py-3 font-semibold">Recall</th>
                  <th className="px-3 py-3 font-semibold">F1</th>
                  <th className="px-3 py-3 font-semibold">ROC-AUC</th>
                  <th className="px-3 py-3 font-semibold">Duration</th>
                  <th className="px-3 py-3 font-semibold">Champion</th>
                  <th className="px-3 py-3 font-semibold">Rank</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {comparison.items.map((item) => {
                  const metrics = comparison.metric_source === "test" ? item.test_metrics : item.validation_metrics;
                  const isBest =
                    comparison.comparability_status === "directly_comparable"
                    && item.primary_metric_value !== null
                    && item.primary_metric_value === maxValue;
                  return (
                    <tr key={item.training_run_id} className={isBest ? "bg-emerald-50/60" : undefined}>
                      <td className="px-3 py-4 font-medium text-ink">{item.model_display_name}</td>
                      <td className="px-3 py-4 text-slate-700">{formatModelFamily(item.model_family)}</td>
                      <td className="px-3 py-4 text-slate-700">{item.dataset_identifiers.join(", ") || "All imported"}</td>
                      <td className="px-3 py-4 text-slate-700">{item.text_composition_mode ?? "N/A"}</td>
                      <td className="px-3 py-4 text-slate-700">{formatMetric(metrics?.accuracy)}</td>
                      <td className="px-3 py-4 text-slate-700">{formatMetric(metrics?.precision)}</td>
                      <td className="px-3 py-4 text-slate-700">{formatMetric(metrics?.recall)}</td>
                      <td className="px-3 py-4 text-slate-700">{formatMetric(metrics?.f1)}</td>
                      <td className="px-3 py-4 text-slate-700">{formatMetric(metrics?.roc_auc)}</td>
                      <td className="px-3 py-4 text-slate-700">{item.training_duration_seconds?.toFixed(2) ?? "N/A"}s</td>
                      <td className="px-3 py-4 text-slate-700">{item.is_champion ? "Champion" : "No"}</td>
                      <td className="px-3 py-4 text-slate-700">{item.rank ?? "N/A"}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      ) : null}
    </section>
  );
}
