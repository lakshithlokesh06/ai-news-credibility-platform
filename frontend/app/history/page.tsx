import Link from "next/link";
import { BarChart3, History, Search, Trash2 } from "lucide-react";

import { EmptyState } from "@/components/EmptyState";
import { PageHeader } from "@/components/PageHeader";
import {
  AnalysisHistorySummary,
  HistoryStatistics,
  PaginatedResponse,
  ReviewStatistics,
  fetchFromApi,
  formatExplanationMethod,
  formatMetric,
  formatModelFamily,
  formatModelType,
  formatPercentage,
  formatReviewStatus,
} from "@/lib/api";

export const dynamic = "force-dynamic";

type HistoryPageProps = {
  searchParams?: Promise<Record<string, string | string[] | undefined>>;
};

function firstValue(value: string | string[] | undefined) {
  return Array.isArray(value) ? value[0] : value;
}

function buildHistoryQuery(params: Record<string, string | string[] | undefined>) {
  const query = new URLSearchParams();
  for (const key of ["predicted_label", "model_family", "model_type", "explanation_available", "review_filter", "search"]) {
    const value = firstValue(params[key]);
    if (value && value !== "all") {
      query.set(key, value);
    }
  }
  query.set("limit", "50");
  query.set("offset", "0");
  return query.toString();
}

async function loadHistory(params: Record<string, string | string[] | undefined>) {
  try {
    const query = buildHistoryQuery(params);
    const [history, statistics, reviewStatistics] = await Promise.all([
      fetchFromApi<PaginatedResponse<AnalysisHistorySummary>>(`/api/v1/history?${query}`),
      fetchFromApi<HistoryStatistics>("/api/v1/history/statistics"),
      fetchFromApi<ReviewStatistics>("/api/v1/reviews/statistics"),
    ]);
    return { history, statistics, reviewStatistics };
  } catch {
    return null;
  }
}

export default async function HistoryPage({ searchParams }: HistoryPageProps) {
  const params = (await searchParams) ?? {};
  const data = await loadHistory(params);
  const predictionFilter = firstValue(params.predicted_label) ?? "all";
  const familyFilter = firstValue(params.model_family) ?? "all";
  const modelTypeFilter = firstValue(params.model_type) ?? "all";
  const explanationFilter = firstValue(params.explanation_available) ?? "all";
  const reviewFilter = firstValue(params.review_filter) ?? "all";
  const searchFilter = firstValue(params.search) ?? "";

  return (
    <>
      <PageHeader
        eyebrow="Analysis history"
        title="History"
        description="Review saved article analyses, persisted explanations, and aggregate trends for this local installation."
      />
      <div className="mx-auto w-full max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
        {!data ? (
          <section className="rounded-lg border border-amber-200 bg-amber-50 px-5 py-4 text-sm leading-6 text-amber-900">
            Backend history APIs are not reachable right now.
          </section>
        ) : data.statistics.total_saved_analyses === 0 ? (
          <EmptyState
            icon={History}
            title="No saved analyses yet"
            description="Run an article analysis from the analysis workspace. Saved predictions and explanations will appear here without rerunning the model."
          />
        ) : (
          <div className="grid gap-6">
            <HistoryDashboard statistics={data.statistics} reviewStatistics={data.reviewStatistics} />
            <HistoryFilters
              predictionFilter={predictionFilter}
              familyFilter={familyFilter}
              modelTypeFilter={modelTypeFilter}
              explanationFilter={explanationFilter}
              reviewFilter={reviewFilter}
              searchFilter={searchFilter}
            />
            <HistoryList history={data.history} />
          </div>
        )}
      </div>
    </>
  );
}

function HistoryDashboard({ statistics, reviewStatistics }: { statistics: HistoryStatistics; reviewStatistics: ReviewStatistics }) {
  return (
    <section className="grid gap-4">
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-5">
        <MetricCard label="Saved analyses" value={String(statistics.total_saved_analyses)} />
        <MetricCard label="Likely misinformation" value={String(statistics.likely_fake_count)} helper={formatPercentage(statistics.likely_fake_percentage)} />
        <MetricCard label="Likely credible" value={String(statistics.likely_real_count)} helper={formatPercentage(statistics.likely_real_percentage)} />
        <MetricCard label="Average confidence" value={formatMetric(statistics.average_confidence)} />
        <MetricCard label="Reviewed" value={String(reviewStatistics.reviewed_analyses)} helper={formatPercentage(reviewStatistics.review_coverage_percentage)} />
      </div>
      <div className="grid gap-4 lg:grid-cols-3">
        <DistributionPanel
          title="Prediction distribution"
          items={[
            { name: "Likely misinformation", count: statistics.likely_fake_count, percentage: statistics.likely_fake_percentage },
            { name: "Likely credible", count: statistics.likely_real_count, percentage: statistics.likely_real_percentage },
          ]}
        />
        <DistributionPanel title="Model families" items={statistics.model_family_distribution} />
        <section className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
          <div className="flex items-center gap-2">
            <BarChart3 aria-hidden="true" className="h-4 w-4 text-signal" />
            <h2 className="text-sm font-semibold text-ink">Recent volume</h2>
          </div>
          <div className="mt-4 grid gap-2">
            {statistics.recent_volume.slice(-7).map((item) => {
              const max = Math.max(...statistics.recent_volume.map((volume) => volume.count), 1);
              return (
                <div key={item.date} className="grid gap-1">
                  <div className="flex justify-between text-xs text-slate-500">
                    <span>{item.date}</span>
                    <span>{item.count}</span>
                  </div>
                  <div className="h-2 rounded-full bg-slate-100">
                    <div className="h-2 rounded-full bg-signal" style={{ width: `${Math.max(8, (item.count / max) * 100)}%` }} />
                  </div>
                </div>
              );
            })}
          </div>
        </section>
      </div>
      <p className="rounded-md bg-slate-50 px-4 py-3 text-sm leading-6 text-slate-600">{statistics.interpretation}</p>
    </section>
  );
}

function MetricCard({ label, value, helper }: { label: string; value: string; helper?: string }) {
  return (
    <div className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
      <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">{label}</p>
      <p className="mt-2 text-2xl font-semibold text-ink">{value}</p>
      {helper ? <p className="mt-1 text-sm text-slate-500">{helper}</p> : null}
    </div>
  );
}

function DistributionPanel({
  title,
  items,
}: {
  title: string;
  items: Array<{ name: string; count: number; percentage: number | null }>;
}) {
  return (
    <section className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
      <h2 className="text-sm font-semibold text-ink">{title}</h2>
      <div className="mt-4 grid gap-3">
        {items.map((item) => (
          <div key={item.name} className="grid gap-1">
            <div className="flex justify-between gap-3 text-sm">
              <span className="text-slate-700">{item.name}</span>
              <span className="text-slate-500">
                {item.count} / {formatPercentage(item.percentage)}
              </span>
            </div>
            <div className="h-2 rounded-full bg-slate-100">
              <div className="h-2 rounded-full bg-ink" style={{ width: `${Math.max(0, item.percentage ?? 0)}%` }} />
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}

function HistoryFilters({
  predictionFilter,
  familyFilter,
  modelTypeFilter,
  explanationFilter,
  reviewFilter,
  searchFilter,
}: {
  predictionFilter: string;
  familyFilter: string;
  modelTypeFilter: string;
  explanationFilter: string;
  reviewFilter: string;
  searchFilter: string;
}) {
  return (
    <form className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-[1.2fr_1fr_1fr_1fr_1fr_1fr]">
        <label className="grid gap-2">
          <span className="text-xs font-semibold uppercase tracking-wide text-slate-500">Search</span>
          <span className="relative">
            <Search aria-hidden="true" className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
            <input
              name="search"
              defaultValue={searchFilter}
              placeholder="Headline or article text"
              className="h-10 w-full rounded-md border border-slate-300 pl-9 pr-3 text-sm text-slate-700"
            />
          </span>
        </label>
        <FilterSelect label="Prediction" name="predicted_label" value={predictionFilter} options={[["all", "All"], ["REAL", "Likely credible"], ["FAKE", "Likely misinformation"]]} />
        <FilterSelect label="Model family" name="model_family" value={familyFilter} options={[["all", "All"], ["classical", "Classical"], ["transformer", "Transformer"]]} />
        <FilterSelect label="Model type" name="model_type" value={modelTypeFilter} options={[["all", "All"], ["logistic_regression", "Logistic Regression"], ["linear_svm", "Linear SVM"], ["distilbert", "DistilBERT"]]} />
        <FilterSelect label="Explanation" name="explanation_available" value={explanationFilter} options={[["all", "All"], ["true", "Available"], ["false", "Missing"]]} />
        <FilterSelect label="Review" name="review_filter" value={reviewFilter} options={[["all", "All"], ["reviewed", "Reviewed"], ["unreviewed", "Unreviewed"], ["correct", "Correct"], ["incorrect", "Incorrect"]]} />
      </div>
      <div className="mt-4 flex flex-wrap gap-3">
        <button type="submit" className="rounded-md bg-ink px-4 py-2 text-sm font-semibold text-white">Apply filters</button>
        <Link href="/history" className="rounded-md border border-slate-300 px-4 py-2 text-sm font-semibold text-ink">Reset</Link>
      </div>
    </form>
  );
}

function FilterSelect({
  label,
  name,
  value,
  options,
}: {
  label: string;
  name: string;
  value: string;
  options: Array<[string, string]>;
}) {
  return (
    <label className="grid gap-2">
      <span className="text-xs font-semibold uppercase tracking-wide text-slate-500">{label}</span>
      <select name={name} defaultValue={value} className="h-10 rounded-md border border-slate-300 bg-white px-3 text-sm text-slate-700">
        {options.map(([optionValue, optionLabel]) => (
          <option key={optionValue} value={optionValue}>{optionLabel}</option>
        ))}
      </select>
    </label>
  );
}

function HistoryList({ history }: { history: PaginatedResponse<AnalysisHistorySummary> }) {
  if (history.total === 0) {
    return (
      <EmptyState
        icon={History}
        title="No matching analyses"
        description="Adjust the filters to find saved predictions and explanations."
      />
    );
  }

  return (
    <section className="grid gap-3">
      {history.items.map((item) => (
        <article key={item.id} className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
          <div className="grid gap-4 lg:grid-cols-[1fr_auto]">
            <div>
              <div className="flex flex-wrap items-center gap-2">
                <span className={item.predicted_label === "FAKE" ? "rounded-md bg-rose-50 px-2 py-1 text-xs font-semibold text-rose-800" : "rounded-md bg-emerald-50 px-2 py-1 text-xs font-semibold text-emerald-800"}>
                  {item.predicted_label === "FAKE" ? "Likely misinformation" : "Likely credible"}
                </span>
                <span className="rounded-md bg-slate-100 px-2 py-1 text-xs font-medium text-slate-600">
                  {item.explanation_available ? "Explanation saved" : "No explanation"}
                </span>
                <span className={reviewBadgeClass(item.review)}>
                  {formatReviewStatus(item.review)}
                </span>
              </div>
              <h2 className="mt-3 text-lg font-semibold text-ink">{item.title || "Untitled analysis"}</h2>
              {item.article_preview ? <p className="mt-2 text-sm leading-6 text-slate-600">{item.article_preview}</p> : null}
              <div className="mt-3 flex flex-wrap gap-x-4 gap-y-2 text-xs text-slate-500">
                <span>{formatModelFamily(item.model_family)} / {item.model_name ?? formatModelType(item.model_type)}</span>
                <span>Model Confidence {formatMetric(item.confidence)}</span>
                <span>{new Date(item.created_at).toLocaleString()}</span>
                {item.explanation_method ? <span>{formatExplanationMethod(item.explanation_method)}</span> : null}
              </div>
            </div>
            <div className="flex items-start gap-2">
              <Link href={`/history/${item.id}`} className="rounded-md border border-slate-300 px-4 py-2 text-sm font-semibold text-ink">View</Link>
              <span className="inline-flex h-9 w-9 items-center justify-center rounded-md border border-slate-200 text-slate-400" title="Delete is available from detail view">
                <Trash2 aria-hidden="true" className="h-4 w-4" />
              </span>
            </div>
          </div>
        </article>
      ))}
    </section>
  );
}

function reviewBadgeClass(review: AnalysisHistorySummary["review"]) {
  if (review.status === "unreviewed") {
    return "rounded-md bg-slate-100 px-2 py-1 text-xs font-medium text-slate-600";
  }
  if (review.is_prediction_correct) {
    return "rounded-md bg-emerald-50 px-2 py-1 text-xs font-semibold text-emerald-800";
  }
  return "rounded-md bg-rose-50 px-2 py-1 text-xs font-semibold text-rose-800";
}
