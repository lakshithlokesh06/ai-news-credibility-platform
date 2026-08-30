export type ArticleLabel = "REAL" | "FAKE";
export type ImportStatus = "PENDING" | "RUNNING" | "COMPLETED" | "FAILED";

export type DistributionItem = {
  name: string;
  count: number;
  percentage: number;
};

export type DatasetStatistics = {
  total_articles: number;
  real_count: number;
  fake_count: number;
  real_percentage: number;
  fake_percentage: number;
  articles_missing_titles: number;
  articles_missing_content: number;
  average_article_length: number | null;
  median_article_length: number | null;
  minimum_article_length: number | null;
  maximum_article_length: number | null;
  duplicate_rows_detected: number;
  dataset_distribution: DistributionItem[];
  source_distribution: DistributionItem[];
};

export type DatasetImportRun = {
  id: string;
  dataset_name: string;
  source_filename: string;
  status: ImportStatus;
  total_rows: number;
  successfully_imported_rows: number;
  skipped_rows: number;
  invalid_rows: number;
  duplicate_rows: number;
  started_at: string;
  completed_at: string | null;
  error_summary: string | null;
};

export type NewsArticle = {
  id: string;
  title: string | null;
  content: string | null;
  label: ArticleLabel;
  source_name: string | null;
  author: string | null;
  publication_date: string | null;
  source_url: string | null;
  dataset_name: string;
  external_id: string | null;
  import_run_id: string | null;
  created_at: string;
  updated_at: string;
};

export type ClassicalModelType = "logistic_regression" | "linear_svm";
export type SupportedModelType = ClassicalModelType | "distilbert";
export type ModelFamily = "classical" | "transformer";
export type TrainingRunStatus = "pending" | "training" | "completed" | "failed";
export type ModelLifecycleStatus = "candidate" | "champion" | "archived";

export type MLTrainingRun = {
  id: string;
  model_family: ModelFamily;
  model_type: SupportedModelType;
  base_model_name: string | null;
  model_display_name: string;
  description: string | null;
  tags: string[];
  explainability_supported: boolean;
  explanation_method: string | null;
  status: TrainingRunStatus;
  lifecycle_status: ModelLifecycleStatus | null;
  preprocessing_config: Record<string, unknown>;
  text_composition_config: Record<string, unknown>;
  tfidf_config: Record<string, unknown>;
  transformer_config: Record<string, unknown>;
  model_hyperparameters: Record<string, unknown>;
  split_config: Record<string, unknown>;
  random_seed: number;
  train_count: number;
  validation_count: number;
  test_count: number;
  dataset_article_count: number;
  dataset_identifiers: string[];
  split_distributions: Record<string, unknown>;
  validation_metrics: MetricSet | null;
  test_metrics: MetricSet | null;
  artifact_path: string | null;
  artifact_checksum: string | null;
  artifact_version: string | null;
  probability_method: string | null;
  device_used: string | null;
  training_duration_seconds: number | null;
  environment_versions: Record<string, string>;
  champion_promoted_at: string | null;
  error_summary: string | null;
  started_at: string;
  completed_at: string | null;
  created_at: string;
};

export type MetricSet = {
  accuracy: number | null;
  precision: number | null;
  recall: number | null;
  f1: number | null;
  roc_auc: number | null;
  confusion_matrix: number[][];
  class_metrics: Record<string, Record<string, number | null>>;
  support: Record<string, number>;
};

export type ModelComparisonItem = {
  training_run_id: string;
  model_display_name: string;
  model_family: ModelFamily;
  model_type: SupportedModelType;
  base_model_name: string | null;
  explainability_supported: boolean;
  explanation_method: string | null;
  status: TrainingRunStatus;
  validation_metrics: MetricSet | null;
  test_metrics: MetricSet | null;
  primary_metric_name: string;
  primary_metric_value: number | null;
  lifecycle_status: ModelLifecycleStatus | null;
  is_champion: boolean;
  dataset_identifiers: string[];
  text_composition_mode: string | null;
  rank: number | null;
  comparability_status: string;
  comparability_warnings: string[];
};

export type ModelComparison = {
  metric_source: string;
  primary_metric: string;
  items: ModelComparisonItem[];
  recommended_training_run_id: string | null;
  recommendation_note: string | null;
  comparability_status: string;
  comparability_warnings: string[];
};

export type PredictionResponse = {
  training_run_id: string;
  analysis_id: string | null;
  model_family: ModelFamily;
  model_type: SupportedModelType;
  model_name: string | null;
  predicted_label: ArticleLabel;
  real_probability: number | null;
  fake_probability: number | null;
  confidence: number | null;
  probability_method: string | null;
  message: string;
};

export type InfluentialItem = {
  text: string;
  attribution_score: number;
  attribution_magnitude: number;
  direction: ArticleLabel;
  rank: number;
  start_offset: number | null;
  end_offset: number | null;
  source_tokens: string[] | null;
};

export type ExplanationResponse = {
  training_run_id: string;
  analysis_id: string | null;
  model_family: ModelFamily;
  model_type: SupportedModelType;
  model_name: string | null;
  predicted_label: ArticleLabel;
  real_probability: number | null;
  fake_probability: number | null;
  confidence: number | null;
  probability_method: string | null;
  explanation_method: string;
  explained_class: ArticleLabel;
  influences_toward_real: InfluentialItem[];
  influences_toward_fake: InfluentialItem[];
  limitations: string[];
  message: string;
};

export type AnalysisHistorySummary = {
  id: string;
  training_run_id: string | null;
  model_family: ModelFamily;
  model_type: SupportedModelType;
  model_name: string | null;
  model_display_name: string;
  title: string | null;
  article_preview: string | null;
  predicted_label: ArticleLabel;
  real_probability: number | null;
  fake_probability: number | null;
  confidence: number | null;
  explanation_available: boolean;
  explanation_method: string | null;
  created_at: string;
  updated_at: string;
};

export type AnalysisExplanationDetail = {
  explanation_method: string;
  explained_class: ArticleLabel;
  influences_toward_real: InfluentialItem[];
  influences_toward_fake: InfluentialItem[];
  limitations: string[];
  message: string | null;
  generated_at: string;
};

export type AnalysisHistoryDetail = {
  id: string;
  training_run_id: string | null;
  model_family: ModelFamily;
  model_type: SupportedModelType;
  model_name: string | null;
  model_display_name: string;
  title: string | null;
  content: string | null;
  text_composition_mode: string | null;
  predicted_label: ArticleLabel;
  real_probability: number | null;
  fake_probability: number | null;
  confidence: number | null;
  probability_method: string | null;
  explanation_status: string;
  explanation: AnalysisExplanationDetail | null;
  created_at: string;
  updated_at: string;
};

export type HistoryDistributionItem = {
  name: string;
  count: number;
  percentage: number | null;
};

export type TrainingRunHistoryItem = {
  training_run_id: string | null;
  model_display_name: string;
  count: number;
  percentage: number | null;
};

export type RecentHistoryVolumeItem = {
  date: string;
  count: number;
};

export type HistoryStatistics = {
  total_saved_analyses: number;
  likely_real_count: number;
  likely_fake_count: number;
  likely_real_percentage: number | null;
  likely_fake_percentage: number | null;
  average_confidence: number | null;
  average_real_confidence: number | null;
  average_fake_confidence: number | null;
  analyses_with_explanations: number;
  analyses_without_explanations: number;
  model_family_distribution: HistoryDistributionItem[];
  model_type_distribution: HistoryDistributionItem[];
  training_run_distribution: TrainingRunHistoryItem[];
  recent_volume: RecentHistoryVolumeItem[];
  interpretation: string;
};

export type DriftMetricStatus = "stable" | "warning" | "drift_detected" | "insufficient_data";
export type MonitoringStatus = "healthy" | "watch" | "drift_detected" | "insufficient_data";

export type MonitoringProfile = {
  id: string;
  training_run_id: string;
  profile_version: string;
  status: string;
  sample_count: number;
  reference_statistics: Record<string, unknown>;
  reference_label_distribution: Record<string, number>;
  feature_metadata: Record<string, unknown>;
  created_at: string;
  updated_at: string;
};

export type MonitoringMetric = {
  metric_name: string;
  metric_value: number | null;
  warning_threshold: number | null;
  drift_threshold: number | null;
  status: DriftMetricStatus;
  interpretation: string;
};

export type ConfidenceMonitoring = {
  average_confidence: number | null;
  median_confidence: number | null;
  low_confidence_rate: number | null;
  high_confidence_rate: number | null;
  average_real_probability: number | null;
  average_fake_probability: number | null;
  confidence_distribution: number[];
  confidence_shift: MonitoringMetric;
};

export type UsageMonitoring = {
  total_analyses: number;
  analyses_in_window: number;
  real_prediction_count: number;
  fake_prediction_count: number;
  explanation_generation_rate: number | null;
  average_confidence: number | null;
  last_used_at: string | null;
  recent_volume: RecentHistoryVolumeItem[];
};

export type ModelMonitoring = {
  training_run_id: string;
  model_display_name: string;
  model_family: ModelFamily;
  model_type: SupportedModelType;
  model_name: string | null;
  monitoring_window: Record<string, number>;
  reference_profile_status: string;
  reference_profile: MonitoringProfile | null;
  sample_counts: Record<string, number>;
  input_drift_metrics: MonitoringMetric[];
  prediction_drift: MonitoringMetric;
  confidence_metrics: ConfidenceMonitoring;
  usage_metrics: UsageMonitoring;
  overall_status: MonitoringStatus;
  status_reasons: string[];
  limitations: string[];
};

export type MonitoringOverviewItem = {
  training_run_id: string;
  model_display_name: string;
  model_family: ModelFamily;
  model_type: SupportedModelType;
  model_name: string | null;
  recent_analysis_count: number;
  monitoring_status: MonitoringStatus;
  prediction_drift_status: DriftMetricStatus;
  input_drift_status: DriftMetricStatus;
  average_confidence: number | null;
  last_analyzed_at: string | null;
};

export type MonitoringOverview = {
  items: MonitoringOverviewItem[];
  total_completed_models: number;
  healthy_models: number;
  models_needing_attention: number;
  insufficient_data_models: number;
  recent_analyses: number;
  limitations: string[];
};

export type LifecycleEvent = {
  id: string;
  training_run_id: string;
  previous_champion_id: string | null;
  event_type: "promoted" | "demoted" | "archived" | "restored" | string;
  from_status: string | null;
  to_status: string | null;
  note: string | null;
  created_at: string;
};

export type ExperimentSummary = {
  training_run_id: string;
  model_display_name: string;
  description: string | null;
  tags: string[];
  model_family: ModelFamily;
  model_type: SupportedModelType;
  base_model_name: string | null;
  execution_status: TrainingRunStatus;
  lifecycle_status: ModelLifecycleStatus | null;
  is_champion: boolean;
  dataset_identifiers: string[];
  text_composition_mode: string | null;
  random_seed: number;
  train_count: number;
  validation_count: number;
  test_count: number;
  primary_test_metric: number | null;
  artifact_version: string | null;
  artifact_checksum: string | null;
  explainability_supported: boolean;
  explanation_method: string | null;
  monitoring_available: boolean;
  trained_at: string | null;
  created_at: string;
};

export type ExperimentDetail = ExperimentSummary & {
  preprocessing_config: Record<string, unknown>;
  text_composition_config: Record<string, unknown>;
  tfidf_config: Record<string, unknown>;
  transformer_config: Record<string, unknown>;
  model_hyperparameters: Record<string, unknown>;
  split_config: Record<string, unknown>;
  split_distributions: Record<string, unknown>;
  validation_metrics: MetricSet | null;
  test_metrics: MetricSet | null;
  artifact_path: string | null;
  probability_method: string | null;
  device_used: string | null;
  training_duration_seconds: number | null;
  environment_versions: Record<string, string>;
  champion_promoted_at: string | null;
  lifecycle_events: LifecycleEvent[];
};

export type ExperimentComparisonItem = {
  training_run_id: string;
  model_display_name: string;
  model_family: ModelFamily;
  model_type: SupportedModelType;
  base_model_name: string | null;
  lifecycle_status: ModelLifecycleStatus | null;
  is_champion: boolean;
  dataset_identifiers: string[];
  text_composition_mode: string | null;
  split_config: Record<string, unknown>;
  validation_metrics: MetricSet | null;
  test_metrics: MetricSet | null;
  training_duration_seconds: number | null;
  primary_metric_name: string;
  primary_metric_value: number | null;
  rank: number | null;
  difference_from_best: number | null;
};

export type ExperimentComparison = {
  metric_source: "validation" | "test";
  primary_metric: "accuracy" | "precision" | "recall" | "f1" | "roc_auc";
  comparability_status: "directly_comparable" | "limited_comparability" | "insufficient_metrics";
  comparability_warnings: string[];
  champion_training_run_id: string | null;
  items: ExperimentComparisonItem[];
};

export type ChampionResponse = {
  champion: ExperimentSummary | null;
};

export type LifecycleActionResponse = {
  training_run_id: string;
  lifecycle_status: ModelLifecycleStatus | null;
  previous_champion_id?: string | null;
  message: string;
};

export type PaginatedResponse<T> = {
  items: T[];
  total: number;
  limit: number;
  offset: number;
};

export const apiBaseUrl =
  process.env.NEXT_PUBLIC_API_BASE_URL?.replace(/\/$/, "") ?? "http://localhost:8000";

export async function fetchFromApi<T>(path: string): Promise<T> {
  const response = await fetch(`${apiBaseUrl}${path}`, {
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error(`API request failed with status ${response.status}`);
  }

  return response.json() as Promise<T>;
}

export function formatModelType(modelType: SupportedModelType) {
  if (modelType === "logistic_regression") {
    return "Logistic Regression";
  }
  if (modelType === "linear_svm") {
    return "Linear SVM";
  }
  return "DistilBERT Transformer";
}

export function formatModelFamily(modelFamily: ModelFamily) {
  return modelFamily === "classical" ? "Classical" : "Transformer";
}

export function formatMetric(value: number | null | undefined) {
  if (value === null || value === undefined) {
    return "N/A";
  }
  return value.toFixed(3);
}

export function formatPercentage(value: number | null | undefined) {
  if (value === null || value === undefined) {
    return "N/A";
  }
  return `${value.toFixed(1)}%`;
}

export function formatMonitoringStatus(status: MonitoringStatus | DriftMetricStatus | string) {
  const labels: Record<string, string> = {
    healthy: "Healthy",
    watch: "Watch",
    stable: "Stable",
    warning: "Warning",
    drift_detected: "Drift detected",
    insufficient_data: "Insufficient data",
  };
  return labels[status] ?? status;
}

export function formatLifecycleStatus(status: ModelLifecycleStatus | null | undefined) {
  if (!status) {
    return "Not eligible";
  }
  const labels: Record<ModelLifecycleStatus, string> = {
    candidate: "Candidate",
    champion: "Champion",
    archived: "Archived",
  };
  return labels[status];
}

export function formatExplanationMethod(method: string | null | undefined) {
  if (!method) {
    return "Not supported";
  }
  const labels: Record<string, string> = {
    coefficient_tfidf_local: "TF-IDF feature attribution",
    coefficient_tfidf_local_or_shap: "TF-IDF feature attribution / SHAP",
    shap_linear_logistic: "SHAP linear attribution",
    linear_svm_underlying_decision_function: "Linear SVM feature attribution",
    shap_text: "SHAP text attribution",
  };
  return labels[method] ?? method;
}
