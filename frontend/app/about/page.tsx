import { ShieldCheck } from "lucide-react";

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
            <h2 className="text-xl font-semibold text-ink">Foundation only</h2>
          </div>
          <p className="mt-4 text-sm leading-6 text-slate-600">
            The current application contains routing, layout, configuration,
            database setup, and test scaffolding. It does not include NLP
            preprocessing, trained models, model inference, prediction history,
            or explainability logic.
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
      </div>
    </>
  );
}

