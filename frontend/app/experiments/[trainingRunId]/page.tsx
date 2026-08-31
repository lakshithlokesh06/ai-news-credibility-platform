import Link from "next/link";
import { ArrowLeft, BarChart3, Boxes, Database, FlaskConical, MonitorDot, Settings, Trophy } from "lucide-react";

import { EmptyState } from "@/components/EmptyState";
import { LifecycleActions } from "@/components/LifecycleActions";
import { PageHeader } from "@/components/PageHeader";
import {
  ChampionResponse,
  ExperimentDetail,
  MetricSet,
  ReviewStatistics,
  fetchFromApi,
  formatExplanationMethod,
  formatLifecycleStatus,
  formatMetric,
  formatModelFamily,
  formatModelType,
} from "@/lib/api";

export const dynamic = "force-dynamic";

type ExperimentDetailPageProps = {
  params: Promise<{ trainingRunId: string }>;
};

async function loadExperiment(trainingRunId: string) {
  try {
    const [experiment, champion, reviewStatistics] = await Promise.all([
      fetchFromApi<ExperimentDetail>(`/api/v1/experiments/${trainingRunId}`),
      fetchFromApi<ChampionResponse>("/api/v1/models/champion"),
      fetchFromApi<ReviewStatistics>("/api/v1/reviews/statistics"),
    ]);
    return { experiment, champion, reviewStatistics };
  } catch {
    return null;
  }
}

export default async function ExperimentDetailPage({ params }: ExperimentDetailPageProps) {
  const { trainingRunId } = await params;
  const data = await loadExperiment(trainingRunId);

  if (!data) {
    return (
      <>
        <PageHeader
          eyebrow="Experiment detail"
          title="Experiment"
          description="This experiment could not be found."
        />
        <div className="mx-auto w-full max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
          <EmptyState
            icon={FlaskConical}
            title="Experiment unavailable"
            description="The training run may be missing, or the experiment API may be unavailable."
          />
        </div>
      </>
    );
  }

  const experiment = data.experiment;
  const reviewedCount =
    data.reviewStatistics.per_training_run.find((item) => item.training_run_id === experiment.training_run_id)?.reviewed_count ?? 0;

  return (
    <>
      <PageHeader
        eyebrow="Experiment detail"
        title={experiment.model_display_name}
        description="Stored run metadata, validation/test metrics, lifecycle state, and artifact references without rerunning training or evaluation."
      />
      <div className="mx-auto grid w-full max-w-7xl gap-6 px-4 py-8 sm:px-6 lg:grid-cols-[1fr_340px] lg:px-8">
        <section className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
          <Link href="/experiments" className="inline-flex items-center gap-2 text-sm font-semibold text-ink">
            <ArrowLeft aria-hidden="true" className="h-4 w-4" />
            Back to experiments
          </Link>
          <div className="mt-6 flex flex-wrap items-center gap-2">
            {experiment.is_champion ? (
              <span className="rounded-md bg-amber-50 px-2 py-1 text-xs font-semibold text-amber-800">Champion</span>
            ) : null}
            <span className="rounded-md bg-slate-100 px-2 py-1 text-xs font-medium text-slate-600">
              {formatLifecycleStatus(experiment.lifecycle_status)}
            </span>
            <span className="rounded-md bg-slate-100 px-2 py-1 text-xs font-medium text-slate-600">
              {experiment.execution_status}
            </span>
          </div>
          <dl className="mt-6 grid gap-4 text-sm md:grid-cols-3">
            <Definition label="Family" value={formatModelFamily(experiment.model_family)} />
            <Definition label="Model" value={experiment.base_model_name ?? formatModelType(experiment.model_type)} />
            <Definition label="Seed" value={String(experiment.random_seed)} />
            <Definition label="Dataset" value={experiment.dataset_identifiers.join(", ") || "All imported"} />
            <Definition label="Text mode" value={experiment.text_composition_mode ?? "N/A"} />
            <Definition label="Duration" value={experiment.training_duration_seconds ? `${experiment.training_duration_seconds.toFixed(2)}s` : "N/A"} />
            <Definition label="Explainability" value={formatExplanationMethod(experiment.explanation_method)} />
            <Definition label="Monitoring" value={experiment.monitoring_available ? "Available" : "No profile yet"} />
            <Definition label="Reviewed samples" value={String(reviewedCount)} />
            <Definition label="Trained" value={experiment.trained_at ? new Date(experiment.trained_at).toLocaleString() : "N/A"} />
          </dl>
        </section>

        <aside className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
          <div className="flex items-center gap-2">
            <Trophy aria-hidden="true" className="h-4 w-4 text-signal" />
            <h2 className="text-lg font-semibold text-ink">Lifecycle</h2>
          </div>
          <p className="mt-3 text-sm leading-6 text-slate-600">
            Champion is the selected application default, not a universal best-model claim.
          </p>
          <div className="mt-5">
            <LifecycleActions
              trainingRunId={experiment.training_run_id}
              modelName={experiment.model_display_name}
              lifecycleStatus={experiment.lifecycle_status}
              executionStatus={experiment.execution_status}
              currentChampion={data.champion.champion}
            />
          </div>
        </aside>

        <MetricSection title="Validation metrics" icon={BarChart3} metrics={experiment.validation_metrics} />
        <MetricSection title="Test metrics" icon={BarChart3} metrics={experiment.test_metrics} />

        <section className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
          <div className="flex items-center gap-2">
            <Database aria-hidden="true" className="h-4 w-4 text-signal" />
            <h2 className="text-lg font-semibold text-ink">Dataset and split</h2>
          </div>
          <dl className="mt-5 grid grid-cols-2 gap-4 text-sm">
            <Definition label="Train" value={String(experiment.train_count)} />
            <Definition label="Validation" value={String(experiment.validation_count)} />
            <Definition label="Test" value={String(experiment.test_count)} />
            <Definition label="Total" value={String(experiment.train_count + experiment.validation_count + experiment.test_count)} />
          </dl>
          <JsonBlock value={{ split_config: experiment.split_config, split_distributions: experiment.split_distributions }} />
        </section>

        <section className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
          <div className="flex items-center gap-2">
            <Settings aria-hidden="true" className="h-4 w-4 text-signal" />
            <h2 className="text-lg font-semibold text-ink">Configuration</h2>
          </div>
          <JsonBlock
            value={{
              preprocessing: experiment.preprocessing_config,
              text_composition: experiment.text_composition_config,
              tfidf: experiment.tfidf_config,
              transformer: experiment.transformer_config,
              hyperparameters: experiment.model_hyperparameters,
            }}
          />
        </section>

        <section className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
          <div className="flex items-center gap-2">
            <Boxes aria-hidden="true" className="h-4 w-4 text-signal" />
            <h2 className="text-lg font-semibold text-ink">Artifact</h2>
          </div>
          <dl className="mt-5 grid gap-3 text-sm">
            <Definition label="Path" value={experiment.artifact_path ?? "N/A"} />
            <Definition label="Version" value={experiment.artifact_version ?? "N/A"} />
            <Definition label="Checksum" value={experiment.artifact_checksum ?? "N/A"} />
            <Definition label="Probability method" value={experiment.probability_method ?? "N/A"} />
            <Definition label="Device" value={experiment.device_used ?? "N/A"} />
          </dl>
        </section>

        <section className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
          <div className="flex items-center gap-2">
            <MonitorDot aria-hidden="true" className="h-4 w-4 text-signal" />
            <h2 className="text-lg font-semibold text-ink">Monitoring and events</h2>
          </div>
          <div className="mt-5 flex flex-wrap gap-3">
            <Link
              href={`/monitoring/${experiment.training_run_id}`}
              className="inline-flex items-center justify-center rounded-md border border-slate-300 px-4 py-2 text-sm font-semibold text-ink"
            >
              Monitoring detail
            </Link>
            <Link
              href={`/performance?training_run_id=${experiment.training_run_id}`}
              className="inline-flex items-center justify-center rounded-md border border-slate-300 px-4 py-2 text-sm font-semibold text-ink"
            >
              Reviewed performance
            </Link>
          </div>
          <div className="mt-5 grid gap-3">
            {experiment.lifecycle_events.length ? (
              experiment.lifecycle_events.map((event) => (
                <div key={event.id} className="rounded-md bg-slate-50 px-4 py-3 text-sm leading-6 text-slate-700">
                  <p className="font-semibold text-ink">{event.event_type}</p>
                  <p>{new Date(event.created_at).toLocaleString()}</p>
                  {event.note ? <p>{event.note}</p> : null}
                </div>
              ))
            ) : (
              <p className="text-sm leading-6 text-slate-600">No lifecycle events recorded yet.</p>
            )}
          </div>
        </section>
      </div>
    </>
  );
}

function MetricSection({ title, icon: Icon, metrics }: { title: string; icon: typeof BarChart3; metrics: MetricSet | null }) {
  return (
    <section className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
      <div className="flex items-center gap-2">
        <Icon aria-hidden="true" className="h-4 w-4 text-signal" />
        <h2 className="text-lg font-semibold text-ink">{title}</h2>
      </div>
      {metrics ? (
        <>
          <dl className="mt-5 grid grid-cols-2 gap-4 text-sm">
            <Definition label="Accuracy" value={formatMetric(metrics.accuracy)} />
            <Definition label="Precision" value={formatMetric(metrics.precision)} />
            <Definition label="Recall" value={formatMetric(metrics.recall)} />
            <Definition label="F1" value={formatMetric(metrics.f1)} />
            <Definition label="ROC-AUC" value={formatMetric(metrics.roc_auc)} />
          </dl>
          {metrics.confusion_matrix ? (
            <div className="mt-5">
              <p className="text-sm font-medium text-slate-700">Confusion matrix</p>
              <div className="mt-2 grid w-48 grid-cols-2 gap-2 text-center text-sm font-semibold">
                {metrics.confusion_matrix.flat().map((value, index) => (
                  <span key={`${title}-${index}`} className="rounded-md bg-surface px-3 py-2 text-ink">
                    {value}
                  </span>
                ))}
              </div>
            </div>
          ) : null}
        </>
      ) : (
        <p className="mt-4 text-sm leading-6 text-slate-600">No persisted metrics for this split.</p>
      )}
    </section>
  );
}

function Definition({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <dt className="text-slate-500">{label}</dt>
      <dd className="mt-1 break-words font-semibold text-ink">{value}</dd>
    </div>
  );
}

function JsonBlock({ value }: { value: unknown }) {
  return (
    <pre className="mt-5 max-h-80 overflow-auto rounded-md bg-slate-950 p-4 text-xs leading-6 text-slate-100">
      {JSON.stringify(value, null, 2)}
    </pre>
  );
}
