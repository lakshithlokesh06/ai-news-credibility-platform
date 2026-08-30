import { Eye, ShieldCheck } from "lucide-react";

import { PageHeader } from "@/components/PageHeader";

const principles = [
  "Model outputs should be framed as probabilistic signals, not proof of truth.",
  "Datasets, preprocessing, model versions, and evaluation methods should be traceable.",
  "API, service, model, and persistence layers should remain independently testable.",
  "Large datasets, generated artifacts, and secrets should stay out of source control.",
];

export default function AboutPage() {
  return (
    <>
      <PageHeader
        eyebrow="Project scope"
        title="About the platform"
        description="This project is a foundation for a responsible AI credibility analysis system built around modular services, open-source model paths, and transparent evaluation."
      />
      <div className="mx-auto grid w-full max-w-7xl gap-6 px-4 py-8 sm:px-6 lg:grid-cols-[0.85fr_1.15fr] lg:px-8">
        <section className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
          <div className="flex items-center gap-3">
            <span className="flex h-10 w-10 items-center justify-center rounded-lg bg-teal-50 text-signal">
              <ShieldCheck aria-hidden="true" className="h-5 w-5" />
            </span>
            <h2 className="text-xl font-semibold text-ink">Current scope</h2>
          </div>
          <p className="mt-4 text-sm leading-6 text-slate-600">
            The current application includes dataset ingestion, canonical REAL
            and FAKE labels, classical and transformer model training,
            evaluation, artifact-backed inference, model comparison, and local
            model explanations with saved analysis history. It does not perform
            external fact-checking, claim verification, web search, scraping,
            RAG, LLM analysis, source reputation scoring, or live news
            ingestion.
          </p>
        </section>
        <section className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
          <h2 className="text-xl font-semibold text-ink">Design principles</h2>
          <div className="mt-5 grid gap-3">
            {principles.map((principle) => (
              <div key={principle} className="rounded-md border border-slate-200 bg-surface px-4 py-3 text-sm leading-6 text-slate-700">
                {principle}
              </div>
            ))}
          </div>
        </section>
        <section className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm lg:col-span-2">
          <div className="flex items-center gap-3">
            <span className="flex h-10 w-10 items-center justify-center rounded-lg bg-teal-50 text-signal">
              <Eye aria-hidden="true" className="h-5 w-5" />
            </span>
            <h2 className="text-xl font-semibold text-ink">Explainability</h2>
          </div>
          <div className="mt-4 grid gap-4 text-sm leading-6 text-slate-600 md:grid-cols-2">
            <p>
              SHAP and feature attribution estimate which words, phrases, or
              tokens moved a trained model toward its output for one specific
              article. They are included so users can inspect model behavior
              instead of treating a prediction as a black box.
            </p>
            <p>
              Attribution is not fact verification. An influential word is not
              automatically true or false; it reflects how the selected trained
              artifact responded to patterns learned from its dataset.
            </p>
          </div>
        </section>
        <section className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm lg:col-span-2">
          <h2 className="text-xl font-semibold text-ink">Saved history</h2>
          <div className="mt-4 grid gap-4 text-sm leading-6 text-slate-600 md:grid-cols-2">
            <p>
              Saved analysis history stores submitted article titles and
              content, model metadata, prediction probabilities, confidence,
              and any normalized explanation results in the configured
              PostgreSQL database.
            </p>
            <p>
              Dataset statistics describe imported labeled training data,
              evaluation metrics describe held-out model performance, and
              history analytics describe only articles analyzed and saved in
              this local application.
            </p>
          </div>
        </section>
      </div>
    </>
  );
}
