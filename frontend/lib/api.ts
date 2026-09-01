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
export type ReviewState = "unreviewed" | "reviewed";
export type ReviewFilter = "all" | "unreviewed" | "reviewed" | "correct" | "incorrect";
export type ConfidenceBucket = "all" | "high" | "low";
export type ClaimStatus = "open" | "reviewed";
export type EvidenceAssessment = "supports" | "contradicts" | "neutral" | "unclear";

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
  review: AnalysisReviewInfo;
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
  review: AnalysisReviewInfo;
  created_at: string;
  updated_at: string;
};

export type AnalysisReviewInfo = {
  status: ReviewState;
  review_id: string | null;
  verified_label: ArticleLabel | null;
  is_prediction_correct: boolean | null;
  reviewer_note: string | null;
  evidence_note: string | null;
  reviewed_at: string | null;
  updated_at: string | null;
};

export type ReviewQueueItem = {
  id: string;
  training_run_id: string | null;
  model_family: ModelFamily;
  model_type: SupportedModelType;
  model_name: string | null;
  model_display_name: string;
  title: string | null;
  article_preview: string | null;
  predicted_label: ArticleLabel;
  confidence: number | null;
  explanation_available: boolean;
  review: AnalysisReviewInfo;
  evidence_summary: AnalysisEvidenceSummary;
  created_at: string;
};

export type ClaimEvidenceCounts = {
  total: number;
  supports: number;
  contradicts: number;
  neutral: number;
  unclear: number;
};

export type EvidenceReference = {
  id: string;
  claim_id: string;
  source_url: string;
  source_title: string | null;
  publisher: string | null;
  publication_date: string | null;
  assessment: EvidenceAssessment;
  evidence_excerpt: string | null;
  reviewer_note: string | null;
  created_at: string;
  updated_at: string;
};

export type AnalysisClaim = {
  id: string;
  analysis_id: string;
  claim_text: string;
  start_offset: number | null;
  end_offset: number | null;
  status: ClaimStatus;
  reviewer_note: string | null;
  evidence_counts: ClaimEvidenceCounts;
  evidence: EvidenceReference[];
  created_at: string;
  updated_at: string;
};

export type AnalysisEvidenceSummary = {
  analysis_id: string;
  total_claims: number;
  claims_with_evidence: number;
  claims_without_evidence: number;
  total_evidence_references: number;
  supporting_evidence_count: number;
  contradicting_evidence_count: number;
  neutral_evidence_count: number;
  unclear_evidence_count: number;
  evidence_coverage_percentage: number | null;
  latest_evidence_updated_at: string | null;
  interpretation: string;
};

export type ClaimsList = {
  items: AnalysisClaim[];
  total: number;
  limit: number;
  offset: number;
};

export type EvidenceStatistics = {
  analyses_with_claims: number;
  total_claims: number;
  total_evidence_records: number;
  claims_with_evidence: number;
  claims_without_evidence: number;
  evidence_coverage_percentage: number | null;
  assessment_distribution: Record<EvidenceAssessment, number>;
  latest_evidence_updated_at: string | null;
  interpretation: string;
};

export type TrainingRunReviewSummary = {
  training_run_id: string | null;
  model_display_name: string;
  model_family: ModelFamily | null;
  model_type: SupportedModelType | null;
  lifecycle_status: ModelLifecycleStatus | null;
  analysis_count: number;
  reviewed_count: number;
  correct_count: number;
  incorrect_count: number;
  review_coverage_percentage: number | null;
  is_champion: boolean;
};

export type ReviewStatistics = {
  total_analyses: number;
  reviewed_analyses: number;
  unreviewed_analyses: number;
  review_coverage_percentage: number | null;
  reviewed_real_count: number;
  reviewed_fake_count: number;
  correct_prediction_count: number;
  incorrect_prediction_count: number;
  per_training_run: TrainingRunReviewSummary[];
  interpretation: string;
};

export type ConfusionMatrix = {
  labels: ArticleLabel[];
  matrix: number[][];
  true_real_pred_real: number;
  true_real_pred_fake: number;
  true_fake_pred_real: number;
  true_fake_pred_fake: number;
  positive_class: ArticleLabel;
};

export type ProductionPerformance = {
  scope: "training_run" | "mixed_model_aggregate";
  training_run_id: string | null;
  model_display_name: string;
  model_family: ModelFamily | null;
  model_type: SupportedModelType | null;
  reviewed_count: number;
  correct_count: number;
  incorrect_count: number;
  accuracy: number | null;
  precision: number | null;
  recall: number | null;
  f1: number | null;
  roc_auc: { value: number | null; available: boolean; reason: string | null };
  confusion_matrix: ConfusionMatrix;
  minimum_reviewed_samples: number;
  sufficiency_status: "insufficient_data" | "preliminary" | "sufficient";
  positive_class: ArticleLabel;
  held_out_test_metrics: MetricSet | null;
  limitations: string[];
};

export type ReliabilityBin = {
  lower_bound: number;
  upper_bound: number;
  sample_count: number;
  mean_confidence: number;
  observed_accuracy: number;
};

export type CalibrationDiagnostics = {
  scope: "training_run" | "mixed_model_aggregate";
  training_run_id: string | null;
  model_display_name: string;
  sample_count: number;
  bin_count: number;
  brier_score: number | null;
  expected_calibration_error: number | null;
  reliability_bins: ReliabilityBin[];
  minimum_reviewed_samples: number;
  sufficiency_status: "insufficient_data" | "preliminary" | "sufficient";
  limitations: string[];
};

export type ErrorAnalysisItem = {
  analysis_id: string;
  training_run_id: string | null;
  model_display_name: string;
  title: string | null;
  article_preview: string | null;
  predicted_label: ArticleLabel;
  verified_label: ArticleLabel;
  confidence: number | null;
  error_type: "false_positive" | "false_negative" | "correct_real" | "correct_fake";
  explanation_available: boolean;
  created_at: string;
  reviewed_at: string;
};

export type ErrorAnalysis = {
  items: ErrorAnalysisItem[];
  total: number;
  limit: number;
  offset: number;
  statistics: {
    average_confidence_correct: number | null;
    average_confidence_incorrect: number | null;
    high_confidence_error_count: number;
    high_confidence_error_rate: number | null;
    low_confidence_error_count: number;
    low_confidence_error_rate: number | null;
    high_confidence_threshold: number;
    low_confidence_threshold: number;
  };
  definitions: Record<string, string>;
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

export function apiErrorMessage(payload: unknown, fallback: string) {
  if (typeof payload === "object" && payload !== null) {
    const record = payload as Record<string, unknown>;
    const error = record.error;
    if (typeof error === "object" && error !== null && "message" in error) {
      return String((error as Record<string, unknown>).message);
    }
    const detail = record.detail;
    if (typeof detail === "string") {
      return detail;
    }
    if (typeof detail === "object" && detail !== null) {
      const detailRecord = detail as Record<string, unknown>;
      if (detailRecord.message) {
        return String(detailRecord.message);
      }
      if (detailRecord.error) {
        return String(detailRecord.error);
      }
    }
  }
  return fallback;
}

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

export function formatTrainingStatus(status: TrainingRunStatus | string) {
  const labels: Record<string, string> = {
    pending: "Pending",
    training: "Running",
    completed: "Completed",
    failed: "Failed",
  };
  return labels[status] ?? status;
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

export function formatReviewStatus(review: AnalysisReviewInfo | null | undefined) {
  if (!review || review.status === "unreviewed") {
    return "Unreviewed";
  }
  if (review.is_prediction_correct === true) {
    return "Correct prediction";
  }
  if (review.is_prediction_correct === false) {
    return "Incorrect prediction";
  }
  return "Reviewed";
}

export function formatReviewedLabel(label: ArticleLabel | null | undefined) {
  if (!label) {
    return "No human-verified label";
  }
  return label === "FAKE" ? "Human-verified FAKE" : "Human-verified REAL";
}

export function formatEvidenceAssessment(assessment: EvidenceAssessment) {
  const labels: Record<EvidenceAssessment, string> = {
    supports: "Supports claim",
    contradicts: "Contradicts claim",
    neutral: "Neutral",
    unclear: "Unclear",
  };
  return labels[assessment];
}

export function formatEvidenceReadiness(summary: AnalysisEvidenceSummary | null | undefined) {
  if (!summary || summary.total_claims === 0) {
    return "No claims";
  }
  if (summary.total_evidence_references === 0) {
    return "Claims added";
  }
  return "Evidence added";
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
