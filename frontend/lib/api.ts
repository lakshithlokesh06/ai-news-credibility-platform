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

