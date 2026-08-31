import Link from "next/link";
import { ClipboardCheck, Search, UserCheck } from "lucide-react";

import { EmptyState } from "@/components/EmptyState";
import { HumanReviewForm } from "@/components/HumanReviewForm";
import { PageHeader } from "@/components/PageHeader";
import {
  PaginatedResponse,
  ReviewQueueItem,
  ReviewStatistics,
  fetchFromApi,
  formatMetric,
  formatModelFamily,
  formatModelType,
  formatPercentage,
  formatReviewStatus,
} from "@/lib/api";

export const dynamic = "force-dynamic";

type ReviewPageProps = {
  searchParams?: Promise<Record<string, string | string[] | undefined>>;
};

function firstValue(value: string | string[] | undefined) {
  return Array.isArray(value) ? value[0] : value;
}

function buildQueueQuery(params: Record<string, string | string[] | undefined>) {
  const query = new URLSearchParams();
  for (const key of ["review_filter", "predicted_label", "model_family", "model_type", "confidence_bucket", "sort", "search"]) {
    const value = firstValue(params[key]);
    if (value && value !== "all") {
      query.set(key, value);
    }
  }
  query.set("limit", "40");
  query.set("offset", "0");
  return query.toString();
}

async function loadReviewQueue(params: Record<string, string | string[] | undefined>) {
  try {
    const query = buildQueueQuery(params);
    const [queue, statistics] = await Promise.all([
      fetchFromApi<PaginatedResponse<ReviewQueueItem> & { sort: string }>(`/api/v1/reviews/queue?${query}`),
      fetchFromApi<ReviewStatistics>("/api/v1/reviews/statistics"),
    ]);
    return { queue, statistics };
  } catch {
    return null;
  }
}

export default async function ReviewPage({ searchParams }: ReviewPageProps) {
  const params = (await searchParams) ?? {};
  const data = await loadReviewQueue(params);
  const reviewFilter = firstValue(params.review_filter) ?? "unreviewed";
  const predictionFilter = firstValue(params.predicted_label) ?? "all";
  const familyFilter = firstValue(params.model_family) ?? "all";
  const modelTypeFilter = firstValue(params.model_type) ?? "all";
  const confidenceBucket = firstValue(params.confidence_bucket) ?? "all";
  const sort = firstValue(params.sort) ?? "recent";
  const search = firstValue(params.search) ?? "";

  return (
    <>
      <PageHeader
        eyebrow="Human review"
        title="Review Queue"
        description="Assign explicit human-verified labels to saved analyses. Reviews never overwrite model predictions."
      />
      <div className="mx-auto grid w-full max-w-7xl gap-6 px-4 py-8 sm:px-6 lg:px-8">
        {!data ? (
          <section className="rounded-lg border border-amber-200 bg-amber-50 px-5 py-4 text-sm leading-6 text-amber-900">
            Backend review APIs are not reachable right now.
          </section>
        ) : (
          <>
            <ReviewSummary statistics={data.statistics} />
            <ReviewFilters
              reviewFilter={reviewFilter}
              predictionFilter={predictionFilter}
              familyFilter={familyFilter}
              modelTypeFilter={modelTypeFilter}
              confidenceBucket={confidenceBucket}
              sort={sort}
              search={search}
            />
            <ReviewQueue queue={data.queue} />
          </>
        )}
      </div>
    </>
  );
}

function ReviewSummary({ statistics }: { statistics: ReviewStatistics }) {
  return (
    <section className="grid gap-4 md:grid-cols-4">
      <MetricCard label="Saved analyses" value={String(statistics.total_analyses)} />
      <MetricCard label="Reviewed" value={String(statistics.reviewed_analyses)} helper={formatPercentage(statistics.review_coverage_percentage)} />
      <MetricCard label="Unreviewed" value={String(statistics.unreviewed_analyses)} />
      <MetricCard label="Incorrect reviewed" value={String(statistics.incorrect_prediction_count)} />
    </section>
  );
}

function ReviewFilters({
  reviewFilter,
  predictionFilter,
  familyFilter,
  modelTypeFilter,
  confidenceBucket,
  sort,
  search,
}: {
  reviewFilter: string;
  predictionFilter: string;
  familyFilter: string;
  modelTypeFilter: string;
  confidenceBucket: string;
  sort: string;
  search: string;
}) {
  return (
    <form className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-[1.2fr_1fr_1fr_1fr_1fr_1fr_1fr]">
        <label className="grid gap-2">
          <span className="text-xs font-semibold uppercase tracking-wide text-slate-500">Search</span>
          <span className="relative">
            <Search aria-hidden="true" className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
            <input
              name="search"
              defaultValue={search}
              placeholder="Headline or preview"
              className="h-10 w-full rounded-md border border-slate-300 pl-9 pr-3 text-sm text-slate-700"
            />
          </span>
        </label>
        <FilterSelect label="Queue" name="review_filter" value={reviewFilter} options={[["unreviewed", "Unreviewed"], ["reviewed", "Reviewed"], ["correct", "Correct"], ["incorrect", "Incorrect"], ["all", "All"]]} />
        <FilterSelect label="Prediction" name="predicted_label" value={predictionFilter} options={[["all", "All"], ["REAL", "Likely credible"], ["FAKE", "Likely misinformation"]]} />
        <FilterSelect label="Family" name="model_family" value={familyFilter} options={[["all", "All"], ["classical", "Classical"], ["transformer", "Transformer"]]} />
        <FilterSelect label="Model" name="model_type" value={modelTypeFilter} options={[["all", "All"], ["logistic_regression", "Logistic Regression"], ["linear_svm", "Linear SVM"], ["distilbert", "DistilBERT"]]} />
        <FilterSelect label="Confidence" name="confidence_bucket" value={confidenceBucket} options={[["all", "All"], ["low", "Low"], ["high", "High"]]} />
        <FilterSelect label="Sort" name="sort" value={sort} options={[["recent", "Recent"], ["low_confidence", "Low confidence"], ["high_confidence", "High confidence"]]} />
      </div>
      <div className="mt-4 flex flex-wrap gap-3">
        <button type="submit" className="rounded-md bg-ink px-4 py-2 text-sm font-semibold text-white">Apply filters</button>
        <Link href="/review" className="rounded-md border border-slate-300 px-4 py-2 text-sm font-semibold text-ink">Reset</Link>
      </div>
    </form>
  );
}

function ReviewQueue({ queue }: { queue: PaginatedResponse<ReviewQueueItem> & { sort: string } }) {
  if (queue.total === 0) {
    return (
      <EmptyState
        icon={ClipboardCheck}
        title="No analyses in this queue"
        description="Adjust the filters or save new analyses from the analysis workspace."
      />
    );
  }

  return (
    <section className="grid gap-4">
      {queue.items.map((item) => (
        <article key={item.id} className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
          <div className="grid gap-5 lg:grid-cols-[1fr_280px]">
            <div>
              <div className="flex flex-wrap items-center gap-2">
                <span className={item.predicted_label === "FAKE" ? "rounded-md bg-rose-50 px-2 py-1 text-xs font-semibold text-rose-800" : "rounded-md bg-emerald-50 px-2 py-1 text-xs font-semibold text-emerald-800"}>
                  Prediction: {item.predicted_label}
                </span>
                <span className="rounded-md bg-slate-100 px-2 py-1 text-xs font-medium text-slate-600">
                  {formatReviewStatus(item.review)}
                </span>
                <span className="rounded-md bg-slate-100 px-2 py-1 text-xs font-medium text-slate-600">
                  {item.explanation_available ? "Explanation saved" : "No explanation"}
                </span>
              </div>
              <h2 className="mt-3 text-lg font-semibold text-ink">{item.title || "Untitled analysis"}</h2>
              {item.article_preview ? <p className="mt-2 text-sm leading-6 text-slate-600">{item.article_preview}</p> : null}
              <div className="mt-3 flex flex-wrap gap-x-4 gap-y-2 text-xs text-slate-500">
                <span>{formatModelFamily(item.model_family)} / {item.model_name ?? formatModelType(item.model_type)}</span>
                <span>Confidence {formatMetric(item.confidence)}</span>
                <span>{new Date(item.created_at).toLocaleString()}</span>
              </div>
              <Link href={`/history/${item.id}`} className="mt-4 inline-flex items-center gap-2 text-sm font-semibold text-ink">
                <UserCheck aria-hidden="true" className="h-4 w-4" />
                Open full analysis
              </Link>
            </div>
            <HumanReviewForm analysisId={item.id} predictedLabel={item.predicted_label} review={item.review} />
          </div>
        </article>
      ))}
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
