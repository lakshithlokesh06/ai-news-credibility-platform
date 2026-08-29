"use client";

import { Loader2, SendHorizontal } from "lucide-react";
import { useState } from "react";

import {
  MLTrainingRun,
  PredictionResponse,
  apiBaseUrl,
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
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  async function submitPrediction() {
    setPrediction(null);
    setError(null);
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
        body: JSON.stringify({ title, content }),
      });
      const payload = await response.json();
      if (!response.ok) {
        setError(typeof payload.detail === "string" ? payload.detail : "Prediction failed.");
        return;
      }
      setPrediction(payload as PredictionResponse);
    } catch {
      setError("Backend inference API is not reachable.");
    } finally {
      setIsLoading(false);
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
            Run classical inference
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
            <p className="rounded-md bg-slate-50 px-4 py-3 leading-6">{prediction.message}</p>
          </div>
        ) : !error ? (
          <p className="mt-5 text-sm leading-6 text-slate-600">
            Predictions will appear here after you train a completed classical model and submit text.
          </p>
        ) : null}
      </aside>
    </div>
  );
}
