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
export type TrainingRunStatus = "pending" | "training" | "completed" | "failed";

export type MLTrainingRun = {
  id: string;
  model_type: ClassicalModelType;
  model_display_name: string;
  status: TrainingRunStatus;
  preprocessing_config: Record<string, unknown>;
  text_composition_config: Record<string, unknown>;
  tfidf_config: Record<string, unknown>;
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
  model_type: ClassicalModelType;
  status: TrainingRunStatus;
  validation_metrics: MetricSet | null;
  test_metrics: MetricSet | null;
  primary_metric_name: string;
  primary_metric_value: number | null;
};

export type ModelComparison = {
  metric_source: string;
  primary_metric: string;
  items: ModelComparisonItem[];
  recommended_training_run_id: string | null;
  recommendation_note: string | null;
};

export type PredictionResponse = {
  training_run_id: string;
  model_type: ClassicalModelType;
  predicted_label: ArticleLabel;
  real_probability: number | null;
  fake_probability: number | null;
  confidence: number | null;
  probability_method: string | null;
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

export function formatModelType(modelType: ClassicalModelType) {
  return modelType === "logistic_regression" ? "Logistic Regression" : "Linear SVM";
}

export function formatMetric(value: number | null | undefined) {
  if (value === null || value === undefined) {
    return "N/A";
  }
  return value.toFixed(3);
}

