"use client";

import { CheckCircle2, Eye, Loader2, SendHorizontal } from "lucide-react";
import { useState } from "react";

import {
  ExplanationResponse,
  InfluentialItem,
  MLTrainingRun,
  PredictionResponse,
  apiBaseUrl,
  formatExplanationMethod,
  formatMetric,
  formatModelFamily,
  formatModelType,
} from "@/lib/api";

type AnalyzeClientProps = {
  models: MLTrainingRun[];
};

export function AnalyzeClient({ models }: AnalyzeClientProps) {
  const [selectedModel, setSelectedModel] = useState(models[0]?.id ?? "");
  const [title, setTitle] = useState("");
  const [content, setContent] = useState("");
  const [prediction, setPrediction] = useState<PredictionResponse | null>(null);
  const [explanation, setExplanation] = useState<ExplanationResponse | null>(null);
  const [analysisId, setAnalysisId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [explanationError, setExplanationError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isExplaining, setIsExplaining] = useState(false);

  async function submitPrediction() {
    setPrediction(null);
    setExplanation(null);
    setAnalysisId(null);
    setError(null);
    setExplanationError(null);
    if (!selectedModel) {
      setError("Select a completed model before running inference.");
      return;
    }
    if (!title.trim() && !content.trim()) {
      setError("Enter a headline, article text, or both.");
      return;
    }
    setIsLoading(true);
    try {
      const response = await fetch(`${apiBaseUrl}/api/v1/ml/models/${selectedModel}/predict`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ title, content, save_to_history: true }),
      });
      const payload = await response.json();
      if (!response.ok) {
        setError(typeof payload.detail === "string" ? payload.detail : "Prediction failed.");
        return;
      }
      const predictionPayload = payload as PredictionResponse;
      setPrediction(predictionPayload);
      setAnalysisId(predictionPayload.analysis_id);
    } catch {
      setError("Backend inference API is not reachable.");
    } finally {
      setIsLoading(false);
    }
  }

  async function requestExplanation() {
    setExplanation(null);
    setExplanationError(null);
    if (!selectedModel || !prediction) {
      setExplanationError("Run an analysis before requesting an explanation.");
      return;
    }
    setIsExplaining(true);
    try {
      const response = await fetch(`${apiBaseUrl}/api/v1/ml/models/${selectedModel}/explain`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          title,
          content,
          analysis_id: analysisId,
          explanation: {
            max_items: 8,
            method: "auto",
            max_transformer_length: 128,
            max_evaluations: 16,
            include_real_support: true,
            include_fake_support: true,
          },
        }),
      });
      const payload = await response.json();
      if (!response.ok) {
        const detail = payload.detail;
        setExplanationError(
          typeof detail === "object" && detail?.message
            ? String(detail.message)
            : "Explanation failed.",
        );
        return;
      }
      const explanationPayload = payload as ExplanationResponse;
      setExplanation(explanationPayload);
      setAnalysisId(explanationPayload.analysis_id ?? analysisId);
    } catch {
      setExplanationError("Backend explanation API is not reachable.");
    } finally {
      setIsExplaining(false);
    }
  }

  const selectedModelRecord = models.find((model) => model.id === selectedModel);
  const predictionText =
    prediction?.predicted_label === "FAKE"
      ? "Model prediction: Likely misinformation"
      : "Model prediction: Likely credible";

  return (
    <div className="mx-auto grid w-full max-w-7xl gap-6 px-4 py-8 sm:px-6 lg:grid-cols-[1fr_360px] lg:px-8">
      <section className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
        <div className="grid gap-4">
          <label className="grid gap-2">
            <span className="text-sm font-medium text-slate-700">Completed model</span>
            <select
              value={selectedModel}
              onChange={(event) => setSelectedModel(event.target.value)}
              className="h-11 rounded-md border border-slate-300 bg-white px-3 text-sm text-slate-700"
            >
              {models.length ? (
                models.map((model) => (
                  <option key={model.id} value={model.id}>
                    {model.model_display_name}
                  </option>
                ))
              ) : (
                <option value="">No completed models available</option>
              )}
            </select>
          </label>
          <label className="grid gap-2">
            <span className="text-sm font-medium text-slate-700">Headline or title</span>
            <input
              value={title}
              onChange={(event) => setTitle(event.target.value)}
              placeholder="Enter a headline"
              className="h-11 rounded-md border border-slate-300 px-3 text-sm text-slate-700 outline-none focus:border-signal"
            />
          </label>
          <label className="grid gap-2">
            <span className="text-sm font-medium text-slate-700">Article text</span>
            <textarea
              value={content}
              onChange={(event) => setContent(event.target.value)}
              rows={10}
              placeholder="Paste article text"
              className="resize-none rounded-md border border-slate-300 px-3 py-3 text-sm text-slate-700 outline-none focus:border-signal"
            />
          </label>
          <button
            type="button"
            onClick={submitPrediction}
            disabled={isLoading || !models.length}
            className="inline-flex w-full items-center justify-center gap-2 rounded-md bg-ink px-5 py-3 text-sm font-semibold text-white disabled:bg-slate-300 sm:w-fit"
          >
            {isLoading ? <Loader2 aria-hidden="true" className="h-4 w-4 animate-spin" /> : <SendHorizontal aria-hidden="true" className="h-4 w-4" />}
            Run analysis
          </button>
        </div>
      </section>

      <aside className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
        <h2 className="text-lg font-semibold text-ink">Inference result</h2>
        {selectedModelRecord ? (
          <p className="mt-3 text-sm text-slate-500">
            Selected: {formatModelFamily(selectedModelRecord.model_family)} /{" "}
            {selectedModelRecord.base_model_name ?? formatModelType(selectedModelRecord.model_type)}
          </p>
        ) : null}
        {error ? (
          <p className="mt-5 rounded-md bg-amber-50 px-4 py-3 text-sm leading-6 text-amber-900">{error}</p>
        ) : null}
        {prediction ? (
          <div className="mt-5 grid gap-3 text-sm text-slate-700">
            <p className="text-xl font-semibold text-ink">{predictionText}</p>
            <p>REAL probability: {formatMetric(prediction.real_probability)}</p>
            <p>FAKE probability: {formatMetric(prediction.fake_probability)}</p>
            <p>Confidence: {formatMetric(prediction.confidence)}</p>
            <p>Model family: {formatModelFamily(prediction.model_family)}</p>
            <p>Model name: {prediction.model_name ?? formatModelType(prediction.model_type)}</p>
            <p>Probability method: {prediction.probability_method ?? "Not available"}</p>
            {analysisId ? (
              <p className="inline-flex items-center gap-2 rounded-md bg-emerald-50 px-3 py-2 text-emerald-800">
                <CheckCircle2 aria-hidden="true" className="h-4 w-4" />
                Analysis saved to history
              </p>
            ) : null}
            <p className="rounded-md bg-slate-50 px-4 py-3 leading-6">{prediction.message}</p>
            <button
              type="button"
              onClick={requestExplanation}
              disabled={isExplaining || !selectedModelRecord?.explainability_supported}
              className="inline-flex items-center justify-center gap-2 rounded-md border border-slate-300 px-4 py-2 text-sm font-semibold text-ink disabled:border-slate-200 disabled:text-slate-400"
            >
              {isExplaining ? <Loader2 aria-hidden="true" className="h-4 w-4 animate-spin" /> : <Eye aria-hidden="true" className="h-4 w-4" />}
              Explain prediction
            </button>
            {!selectedModelRecord?.explainability_supported ? (
              <p className="text-xs leading-5 text-slate-500">This completed model does not expose an explanation method.</p>
            ) : null}
          </div>
        ) : !error ? (
          <p className="mt-5 text-sm leading-6 text-slate-600">
            Predictions will appear here after you train a completed model and submit text.
          </p>
        ) : null}
      </aside>
      <section className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm lg:col-span-2">
        <h2 className="text-lg font-semibold text-ink">Explanation</h2>
        {explanationError ? (
          <p className="mt-4 rounded-md bg-amber-50 px-4 py-3 text-sm leading-6 text-amber-900">{explanationError}</p>
        ) : null}
        {explanation ? (
          <div className="mt-5 grid gap-5">
            <div className="grid gap-2 text-sm text-slate-700 sm:grid-cols-2 lg:grid-cols-4">
              <p>Method: {formatExplanationMethod(explanation.explanation_method)}</p>
              <p>Explained class: {explanation.explained_class}</p>
              <p>REAL probability: {formatMetric(explanation.real_probability)}</p>
              <p>FAKE probability: {formatMetric(explanation.fake_probability)}</p>
            </div>
            <div className="grid gap-4 lg:grid-cols-2">
              <InfluenceList
                title="Influences toward likely misinformation"
                items={explanation.influences_toward_fake}
                tone="fake"
              />
              <InfluenceList
                title="Influences toward likely credible"
                items={explanation.influences_toward_real}
                tone="real"
              />
            </div>
            <HighlightView explanation={explanation} titleText={title} contentText={content} />
            <div className="rounded-md bg-slate-50 px-4 py-3 text-sm leading-6 text-slate-600">
              <p>{explanation.message}</p>
              <ul className="mt-2 list-disc space-y-1 pl-5">
                {explanation.limitations.map((limitation) => (
                  <li key={limitation}>{limitation}</li>
                ))}
              </ul>
            </div>
          </div>
        ) : !explanationError ? (
          <p className="mt-4 text-sm leading-6 text-slate-600">
            After a prediction, request an explanation to see which learned text features or tokens influenced the model.
          </p>
        ) : null}
      </section>
    </div>
  );
}

function InfluenceList({
  title,
  items,
  tone,
}: {
  title: string;
  items: InfluentialItem[];
  tone: "fake" | "real";
}) {
  const maxMagnitude = Math.max(...items.map((item) => item.attribution_magnitude), 0.000001);
  const toneClasses =
    tone === "fake"
      ? "border-rose-200 bg-rose-50 text-rose-950"
      : "border-emerald-200 bg-emerald-50 text-emerald-950";

  return (
    <div className="rounded-md border border-slate-200 p-4">
      <h3 className="text-sm font-semibold text-ink">{title}</h3>
      {items.length ? (
        <div className="mt-4 grid gap-3">
          {items.map((item) => (
            <div key={`${item.direction}-${item.rank}-${item.text}`} className="grid gap-2">
              <div className="flex items-center justify-between gap-3">
                <span className={`rounded-md border px-2 py-1 text-sm font-medium ${toneClasses}`}>{item.text}</span>
                <span className="text-xs text-slate-500">Rank {item.rank}</span>
              </div>
              <div className="h-2 rounded-full bg-slate-100" aria-label={`Relative attribution strength ${item.attribution_magnitude}`}>
                <div
                  className={tone === "fake" ? "h-2 rounded-full bg-rose-500" : "h-2 rounded-full bg-emerald-500"}
                  style={{ width: `${Math.max(8, (item.attribution_magnitude / maxMagnitude) * 100)}%` }}
                />
              </div>
            </div>
          ))}
        </div>
      ) : (
        <p className="mt-4 text-sm leading-6 text-slate-500">No strong local evidence in this direction within the configured limit.</p>
      )}
    </div>
  );
}

function HighlightView({
  explanation,
  titleText,
  contentText,
}: {
  explanation: ExplanationResponse;
  titleText: string;
  contentText: string;
}) {
  const text = [titleText, contentText].filter((value) => value.trim()).join("\n\n");
  const highlights = [...explanation.influences_toward_fake, ...explanation.influences_toward_real]
    .filter((item) => item.start_offset !== null && item.end_offset !== null && item.end_offset <= text.length)
    .sort((left, right) => (left.start_offset ?? 0) - (right.start_offset ?? 0));

  if (!text || highlights.length === 0) {
    return null;
  }

  const segments: Array<
    | { kind: "plain"; text: string; key: string }
    | { kind: "mark"; text: string; key: string; direction: "REAL" | "FAKE" }
  > = [];
  let nextCursor = 0;
  for (const item of highlights) {
    const start = item.start_offset ?? 0;
    const end = item.end_offset ?? start;
    if (start < nextCursor || end <= start) {
      continue;
    }
    const before = text.slice(nextCursor, start);
    const selected = text.slice(start, end);
    if (before) {
      segments.push({ kind: "plain", text: before, key: `plain-${start}` });
    }
    segments.push({ kind: "mark", text: selected, key: `mark-${start}-${end}`, direction: item.direction });
    nextCursor = end;
  }
  const remainder = text.slice(nextCursor);

  return (
    <div className="rounded-md border border-slate-200 p-4">
      <h3 className="text-sm font-semibold text-ink">Article highlights</h3>
      <p className="mt-3 whitespace-pre-wrap text-sm leading-7 text-slate-700">
        {segments.map((segment) =>
          segment.kind === "plain" ? (
            <span key={segment.key}>{segment.text}</span>
          ) : (
            <mark
              key={segment.key}
              className={
                segment.direction === "FAKE"
                  ? "rounded bg-rose-100 px-1 text-rose-950 underline decoration-rose-600 decoration-2"
                  : "rounded bg-emerald-100 px-1 text-emerald-950 underline decoration-emerald-600 decoration-2"
              }
              title={segment.direction === "FAKE" ? "Influence toward likely misinformation" : "Influence toward likely credible"}
            >
              {segment.text}
            </mark>
          ),
        )}
        {remainder}
      </p>
    </div>
  );
}
