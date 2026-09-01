import { ArrowLeft, ArrowRight, Database, FileSearch, TableProperties } from "lucide-react";
import Link from "next/link";

import { EmptyState } from "@/components/EmptyState";
import { PageHeader } from "@/components/PageHeader";
import {
  DatasetImportRun,
  DatasetStatistics,
  NewsArticle,
  PaginatedResponse,
  fetchFromApi,
} from "@/lib/api";

export const dynamic = "force-dynamic";

const PAGE_SIZE = 10;

type SearchParams = {
  label?: string;
  dataset?: string;
  source?: string;
  search?: string;
  offset?: string;
};

type DataPageProps = {
  searchParams: Promise<SearchParams>;
};

type DataPayload = {
  stats: DatasetStatistics;
  imports: PaginatedResponse<DatasetImportRun>;
  articles: PaginatedResponse<NewsArticle>;
  error: string | null;
};

function formatNumber(value: number | null) {
  if (value === null) {
    return "N/A";
  }
  return new Intl.NumberFormat("en").format(value);
}

function formatDate(value: string | null) {
  if (!value) {
    return "Not available";
  }
  return new Intl.DateTimeFormat("en", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}

function buildQuery(params: Record<string, string | number | undefined>) {
  const query = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && String(value).trim()) {
      query.set(key, String(value));
    }
  }
  return query.toString();
}

async function loadData(searchParams: SearchParams): Promise<DataPayload> {
  const offset = Math.max(Number(searchParams.offset ?? "0") || 0, 0);
  const articleQuery = buildQuery({
    label: searchParams.label,
    dataset: searchParams.dataset,
    source: searchParams.source,
    search: searchParams.search,
    limit: PAGE_SIZE,
    offset,
  });

  try {
    const [stats, imports, articles] = await Promise.all([
      fetchFromApi<DatasetStatistics>("/api/v1/dataset-statistics"),
      fetchFromApi<PaginatedResponse<DatasetImportRun>>("/api/v1/dataset-imports?limit=5&offset=0"),
      fetchFromApi<PaginatedResponse<NewsArticle>>(`/api/v1/articles?${articleQuery}`),
    ]);
    return { stats, imports, articles, error: null };
  } catch {
    return {
      stats: {
        total_articles: 0,
        real_count: 0,
        fake_count: 0,
        real_percentage: 0,
        fake_percentage: 0,
        articles_missing_titles: 0,
        articles_missing_content: 0,
        average_article_length: null,
        median_article_length: null,
        minimum_article_length: null,
        maximum_article_length: null,
        duplicate_rows_detected: 0,
        dataset_distribution: [],
        source_distribution: [],
      },
      imports: { items: [], total: 0, limit: 5, offset: 0 },
      articles: { items: [], total: 0, limit: PAGE_SIZE, offset },
      error: "Backend data APIs are not reachable right now.",
    };
  }
}

export default async function DataPage({ searchParams }: DataPageProps) {
  const params = await searchParams;
  const payload = await loadData(params);
  const { stats, imports, articles, error } = payload;
  const latestImport = imports.items[0];
  const offset = articles.offset;
  const hasPrevious = offset > 0;
  const hasNext = offset + articles.limit < articles.total;
  const basePageParams = {
    label: params.label,
    dataset: params.dataset,
    source: params.source,
    search: params.search,
  };

  return (
    <>
      <PageHeader
        eyebrow="Dataset foundation"
        title="Data Overview"
        description="Inspect imported article datasets, class balance, import history, and canonical article records from the backend database."
      />

      <div className="mx-auto grid w-full max-w-7xl gap-6 px-4 py-8 sm:px-6 lg:px-8">
        {error ? (
          <section className="rounded-lg border border-amber-200 bg-amber-50 px-5 py-4 text-sm leading-6 text-amber-900">
            {error} Start the FastAPI backend to view live dataset statistics and articles.
          </section>
        ) : null}

        <section className="grid gap-4 md:grid-cols-4">
          {[
            ["Total articles", formatNumber(stats.total_articles)],
            ["REAL", `${formatNumber(stats.real_count)} (${stats.real_percentage}%)`],
            ["FAKE", `${formatNumber(stats.fake_count)} (${stats.fake_percentage}%)`],
            ["Duplicate rows skipped", formatNumber(stats.duplicate_rows_detected)],
          ].map(([label, value]) => (
            <div key={label} className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
              <p className="text-sm font-medium text-slate-500">{label}</p>
              <p className="mt-3 text-2xl font-semibold text-ink">{value}</p>
            </div>
          ))}
        </section>

        <section className="grid gap-6 lg:grid-cols-[1fr_360px]">
          <div className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
            <div className="flex items-center gap-3">
              <span className="flex h-10 w-10 items-center justify-center rounded-lg bg-teal-50 text-signal">
                <Database aria-hidden="true" className="h-5 w-5" />
              </span>
              <div>
                <h2 className="text-lg font-semibold text-ink">Dataset sources</h2>
                <p className="text-sm text-slate-500">Calculated from canonical articles.</p>
              </div>
            </div>
            {stats.dataset_distribution.length ? (
              <div className="mt-5 grid gap-3">
                {stats.dataset_distribution.map((item) => (
                  <div key={item.name} className="rounded-md border border-slate-200 bg-surface px-4 py-3">
                    <div className="flex items-center justify-between gap-4 text-sm">
                      <span className="font-medium text-slate-700">{item.name}</span>
                      <span className="text-slate-500">{item.count} articles</span>
                    </div>
                    <div className="mt-3 h-2 rounded-full bg-slate-200">
                      <div
                        className="h-2 rounded-full bg-signal"
                        style={{ width: `${Math.min(item.percentage, 100)}%` }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="mt-5 text-sm leading-6 text-slate-600">
                No dataset sources have been imported yet.
              </p>
            )}
          </div>

          <aside className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
            <h2 className="text-lg font-semibold text-ink">Latest import</h2>
            {latestImport ? (
              <div className="mt-5 grid gap-3 text-sm text-slate-600">
                <p>
                  <span className="font-medium text-slate-800">Dataset:</span>{" "}
                  {latestImport.dataset_name}
                </p>
                <p>
                  <span className="font-medium text-slate-800">Status:</span>{" "}
                  {latestImport.status}
                </p>
                <p>
                  <span className="font-medium text-slate-800">Imported:</span>{" "}
                  {latestImport.successfully_imported_rows} of {latestImport.total_rows}
                </p>
                <p>
                  <span className="font-medium text-slate-800">Completed:</span>{" "}
                  {formatDate(latestImport.completed_at)}
                </p>
              </div>
            ) : (
              <p className="mt-5 text-sm leading-6 text-slate-600">
                Import runs will appear after a CSV is imported through the backend API.
              </p>
            )}
          </aside>
        </section>

        <section className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
          <div className="flex flex-col gap-4 border-b border-slate-200 pb-5 lg:flex-row lg:items-center lg:justify-between">
            <div className="flex items-center gap-3">
              <span className="flex h-10 w-10 items-center justify-center rounded-lg bg-teal-50 text-signal">
                <TableProperties aria-hidden="true" className="h-5 w-5" />
              </span>
              <div>
                <h2 className="text-lg font-semibold text-ink">Article browser</h2>
                <p className="text-sm text-slate-500">Paginated canonical article records.</p>
              </div>
            </div>
            <form className="grid gap-2 sm:grid-cols-2 lg:grid-cols-5">
              <select
                aria-label="Filter by label"
                name="label"
                defaultValue={params.label ?? ""}
                className="h-10 rounded-md border border-slate-300 bg-white px-3 text-sm text-slate-700"
              >
                <option value="">All labels</option>
                <option value="REAL">REAL</option>
                <option value="FAKE">FAKE</option>
              </select>
              <input
                aria-label="Filter by dataset"
                name="dataset"
                defaultValue={params.dataset ?? ""}
                placeholder="Dataset"
                className="h-10 rounded-md border border-slate-300 px-3 text-sm text-slate-700"
              />
              <input
                aria-label="Filter by source"
                name="source"
                defaultValue={params.source ?? ""}
                placeholder="Source"
                className="h-10 rounded-md border border-slate-300 px-3 text-sm text-slate-700"
              />
              <input
                aria-label="Search articles"
                name="search"
                defaultValue={params.search ?? ""}
                placeholder="Search title/text"
                className="h-10 rounded-md border border-slate-300 px-3 text-sm text-slate-700"
              />
              <button className="h-10 rounded-md bg-ink px-4 text-sm font-semibold text-white" type="submit">
                Filter
              </button>
            </form>
          </div>

          {articles.items.length ? (
            <div className="mt-5 overflow-x-auto">
              <table className="min-w-full divide-y divide-slate-200 text-left text-sm">
                <thead>
                  <tr className="text-xs uppercase tracking-wide text-slate-500">
                    <th className="px-3 py-3 font-semibold">Headline</th>
                    <th className="px-3 py-3 font-semibold">Label</th>
                    <th className="px-3 py-3 font-semibold">Dataset</th>
                    <th className="px-3 py-3 font-semibold">Source</th>
                    <th className="px-3 py-3 font-semibold">Published</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {articles.items.map((article) => (
                    <tr key={article.id}>
                      <td className="max-w-md px-3 py-4 font-medium text-ink">
                        {article.title || "Untitled article"}
                      </td>
                      <td className="px-3 py-4">
                        <span className="rounded-md bg-slate-100 px-2 py-1 text-xs font-semibold text-slate-700">
                          {article.label}
                        </span>
                      </td>
                      <td className="px-3 py-4 text-slate-600">{article.dataset_name}</td>
                      <td className="px-3 py-4 text-slate-600">{article.source_name || "Unknown"}</td>
                      <td className="px-3 py-4 text-slate-600">{formatDate(article.publication_date)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
              <div className="mt-5 flex items-center justify-between gap-3 text-sm text-slate-600">
                <p>
                  Showing {offset + 1}-{Math.min(offset + articles.items.length, articles.total)} of{" "}
                  {articles.total}
                </p>
                <div className="flex gap-2">
                  <Link
                    aria-disabled={!hasPrevious}
                    href={
                      hasPrevious
                        ? `/data?${buildQuery({ ...basePageParams, offset: Math.max(offset - PAGE_SIZE, 0) })}`
                        : "/data"
                    }
                    className={`inline-flex h-9 items-center gap-2 rounded-md border px-3 font-medium ${
                      hasPrevious
                        ? "border-slate-300 text-slate-700"
                        : "pointer-events-none border-slate-200 text-slate-300"
                    }`}
                  >
                    <ArrowLeft aria-hidden="true" className="h-4 w-4" />
                    Previous
                  </Link>
                  <Link
                    aria-disabled={!hasNext}
                    href={
                      hasNext
                        ? `/data?${buildQuery({ ...basePageParams, offset: offset + PAGE_SIZE })}`
                        : "/data"
                    }
                    className={`inline-flex h-9 items-center gap-2 rounded-md border px-3 font-medium ${
                      hasNext
                        ? "border-slate-300 text-slate-700"
                        : "pointer-events-none border-slate-200 text-slate-300"
                    }`}
                  >
                    Next
                    <ArrowRight aria-hidden="true" className="h-4 w-4" />
                  </Link>
                </div>
              </div>
            </div>
          ) : (
            <div className="mt-6">
              <EmptyState
                icon={FileSearch}
                title="No articles to browse yet"
                description="Place CSV files in data/raw and import them through the backend API to populate this table."
              />
            </div>
          )}
        </section>
      </div>
    </>
  );
}
