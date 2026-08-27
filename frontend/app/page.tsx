import {
  BarChart3,
  BrainCircuit,
  FileText,
  Gauge,
  SearchCheck,
  ShieldCheck,
  Sparkles,
} from "lucide-react";
import Link from "next/link";

const workflow = [
  "News Article",
  "NLP Analysis",
  "ML Prediction",
  "Confidence",
  "Explainability",
];

const capabilities = [
  {
    title: "News credibility analysis",
    description:
      "A future analysis workspace for reviewing headlines and articles through a consistent model-based workflow.",
    icon: SearchCheck,
  },
  {
    title: "NLP-based text analysis",
    description:
      "Planned preprocessing modules will prepare text features while preserving clear boundaries between data handling and modeling.",
    icon: FileText,
  },
  {
    title: "ML and transformer classification",
    description:
      "The architecture leaves room for classical baselines and transformer classifiers behind shared service interfaces.",
    icon: BrainCircuit,
  },
  {
    title: "Confidence scoring",
    description:
      "Future predictions will expose calibrated confidence estimates as model signals, not as guarantees of truth.",
    icon: Gauge,
  },
  {
    title: "Explainable AI",
    description:
      "Explainability components are planned for surfacing model drivers with appropriate caveats and provenance.",
    icon: Sparkles,
  },
  {
    title: "Model evaluation",
    description:
      "Evaluation pages will compare metrics, datasets, model versions, and validation runs when the ML layer arrives.",
    icon: BarChart3,
  },
];

export default function Home() {
  return (
    <>
      <section className="border-b border-slate-200 bg-white">
        <div className="mx-auto grid w-full max-w-7xl gap-10 px-4 py-16 sm:px-6 lg:grid-cols-[1.05fr_0.95fr] lg:px-8 lg:py-20">
          <div className="flex flex-col justify-center">
            <p className="text-sm font-semibold uppercase tracking-wide text-signal">
              Responsible AI credibility analysis
            </p>
            <h1 className="mt-5 max-w-4xl text-4xl font-semibold leading-tight text-ink sm:text-5xl">
              AI News Credibility and Misinformation Detection Platform
            </h1>
            <p className="mt-6 max-w-2xl text-lg leading-8 text-slate-600">
              A production-ready foundation for a future system that will provide
              model-based credibility and misinformation predictions based on
              learned textual patterns.
            </p>
            <div className="mt-8 flex flex-col gap-3 sm:flex-row">
              <Link
                href="/analyze"
                className="inline-flex items-center justify-center rounded-md bg-ink px-5 py-3 text-sm font-semibold text-white transition hover:bg-slate-800"
              >
                Open analysis workspace
              </Link>
              <Link
                href="/about"
                className="inline-flex items-center justify-center rounded-md border border-slate-300 px-5 py-3 text-sm font-semibold text-ink transition hover:bg-slate-50"
              >
                Read project scope
              </Link>
            </div>
          </div>

          <div className="rounded-lg border border-slate-200 bg-surface p-5 shadow-soft">
            <div className="rounded-md bg-white p-5 shadow-sm">
              <div className="flex items-center gap-3 border-b border-slate-100 pb-4">
                <span className="flex h-10 w-10 items-center justify-center rounded-lg bg-teal-50 text-signal">
                  <ShieldCheck aria-hidden="true" className="h-5 w-5" />
                </span>
                <div>
                  <p className="text-sm font-semibold text-ink">Platform Workflow</p>
                  <p className="text-xs text-slate-500">Future model pipeline</p>
                </div>
              </div>
              <div className="mt-5 grid gap-3">
                {workflow.map((item, index) => (
                  <div key={item} className="flex items-center gap-3">
                    <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-md bg-slate-100 text-xs font-semibold text-slate-700">
                      {index + 1}
                    </span>
                    <div className="flex-1 rounded-md border border-slate-200 bg-white px-4 py-3 text-sm font-medium text-slate-700">
                      {item}
                    </div>
                  </div>
                ))}
              </div>
              <p className="mt-5 rounded-md bg-amber-50 px-4 py-3 text-sm leading-6 text-amber-900">
                This foundation does not classify news yet. It prepares the
                application structure for future open-source ML components.
              </p>
            </div>
          </div>
        </div>
      </section>

      <section className="mx-auto w-full max-w-7xl px-4 py-14 sm:px-6 lg:px-8">
        <div className="max-w-3xl">
          <h2 className="text-3xl font-semibold text-ink">Planned capabilities</h2>
          <p className="mt-4 text-base leading-7 text-slate-600">
            Each capability is represented as a clear future module so the platform
            can grow without mixing API routes, model code, persistence, and UI concerns.
          </p>
        </div>
        <div className="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {capabilities.map((capability) => (
            <article key={capability.title} className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
              <div className="flex h-11 w-11 items-center justify-center rounded-lg bg-teal-50 text-signal">
                <capability.icon aria-hidden="true" className="h-5 w-5" />
              </div>
              <h3 className="mt-5 text-lg font-semibold text-ink">{capability.title}</h3>
              <p className="mt-3 text-sm leading-6 text-slate-600">{capability.description}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="border-y border-slate-200 bg-white">
        <div className="mx-auto grid w-full max-w-7xl gap-6 px-4 py-12 sm:px-6 lg:grid-cols-[0.8fr_1.2fr] lg:px-8">
          <div>
            <h2 className="text-2xl font-semibold text-ink">Responsible framing</h2>
            <p className="mt-4 text-sm leading-6 text-slate-600">
              Future outputs should be interpreted as model estimates based on
              data and learned patterns. Human review, source context, and external
              verification remain essential.
            </p>
          </div>
          <div className="grid gap-3 sm:grid-cols-2">
            {[
              "No paid API dependency is required by this foundation.",
              "No model artifacts or datasets are committed.",
              "No fake prediction data appears in the interface.",
              "No claim is made that the platform proves objective truth.",
            ].map((item) => (
              <div key={item} className="rounded-md border border-slate-200 bg-surface px-4 py-3 text-sm font-medium text-slate-700">
                {item}
              </div>
            ))}
          </div>
        </div>
      </section>
    </>
  );
}
