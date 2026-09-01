"use client";

import { Loader2, Play } from "lucide-react";
import { useState } from "react";

import { apiBaseUrl, apiErrorMessage } from "@/lib/api";

export function TrainingAction() {
  const [modelType, setModelType] = useState("logistic_regression");
  const [textMode, setTextMode] = useState("title_and_content");
  const [status, setStatus] = useState<string | null>(null);
  const [isTraining, setIsTraining] = useState(false);

  async function submitTraining() {
    setIsTraining(true);
    setStatus(null);
    try {
      const response = await fetch(`${apiBaseUrl}/api/v1/ml/training-runs`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          model_type: modelType,
          text_composition: { mode: textMode },
        }),
      });
      const payload = await response.json();
      if (!response.ok) {
        setStatus(apiErrorMessage(payload, "Training could not start."));
        return;
      }
      setStatus("Training completed. Refreshing registry...");
      window.location.reload();
    } catch {
      setStatus("Backend training API is not reachable.");
    } finally {
      setIsTraining(false);
    }
  }

  return (
    <section className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <h2 className="text-lg font-semibold text-ink">Train a baseline</h2>
          <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-600">
            Runs synchronously against imported canonical articles using default split, TF-IDF,
            preprocessing, and hyperparameter settings.
          </p>
        </div>
        <div className="grid gap-3 sm:grid-cols-[180px_190px_auto]">
          <select
            aria-label="Model type"
            value={modelType}
            onChange={(event) => setModelType(event.target.value)}
            className="h-10 rounded-md border border-slate-300 bg-white px-3 text-sm text-slate-700"
          >
            <option value="logistic_regression">Logistic Regression</option>
            <option value="linear_svm">Linear SVM</option>
            <option value="distilbert">DistilBERT Transformer</option>
          </select>
          <select
            aria-label="Text composition mode"
            value={textMode}
            onChange={(event) => setTextMode(event.target.value)}
            className="h-10 rounded-md border border-slate-300 bg-white px-3 text-sm text-slate-700"
          >
            <option value="title_and_content">Title + Content</option>
            <option value="title_only">Title Only</option>
            <option value="content_only">Content Only</option>
          </select>
          <button
            type="button"
            onClick={submitTraining}
            disabled={isTraining}
            className="inline-flex h-10 items-center justify-center gap-2 rounded-md bg-ink px-4 text-sm font-semibold text-white disabled:bg-slate-300"
          >
            {isTraining ? <Loader2 aria-hidden="true" className="h-4 w-4 animate-spin" /> : <Play aria-hidden="true" className="h-4 w-4" />}
            Train
          </button>
        </div>
      </div>
      {status ? (
        <p className="mt-4 rounded-md bg-slate-50 px-4 py-3 text-sm leading-6 text-slate-700">{status}</p>
      ) : null}
      {modelType === "distilbert" ? (
        <p className="mt-4 rounded-md bg-amber-50 px-4 py-3 text-sm leading-6 text-amber-900">
          Transformer fine-tuning can take significantly longer than classical baselines and may need
          Hugging Face model files plus sufficient local memory.
        </p>
      ) : null}
    </section>
  );
}
