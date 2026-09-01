import {
  BrainCircuit,
  ClipboardCheck,
  Eye,
  Gauge,
  GitCompare,
  SearchCheck,
  ShieldCheck,
} from "lucide-react";
import Image from "next/image";
import Link from "next/link";

const workflow = [
  "Article",
  "NLP Processing",
  "ML Prediction",
  "Confidence",
  "Explainability",
  "Human Review",
  "Evidence",
  "Performance Monitoring",
];

const capabilityGroups = [
  {
    title: "Machine Learning",
    icon: BrainCircuit,
    items: ["Logistic Regression", "Calibrated Linear SVM", "DistilBERT"],
  },
  {
    title: "Explainability",
    icon: Eye,
    items: ["SHAP attribution", "Influential phrases/tokens", "Model-behavior caveats"],
  },
  {
    title: "Model Operations",
    icon: GitCompare,
    items: ["Experiment comparison", "Champion lifecycle", "Monitoring and drift diagnostics"],
  },
  {
    title: "Responsible Review",
    icon: ClipboardCheck,
    items: ["Human-verified labels", "Manual claims", "Evidence tracking"],
  },
];

export default function Home() {
  return (
    <>
      <section className="relative isolate min-h-[72vh] overflow-hidden bg-slate-950">
        <Image
          src="/news-credibility-hero.png"
          alt=""
          fill
          priority
          sizes="100vw"
          className="object-cover"
        />
        <div className="absolute inset-0 bg-slate-950/70" />
        <div className="relative mx-auto flex min-h-[72vh] w-full max-w-7xl items-center px-4 py-20 sm:px-6 lg:px-8">
          <div className="max-w-3xl">
            <p className="text-sm font-semibold uppercase tracking-wide text-teal-200">
              ML-based news credibility analysis
            </p>
            <h1 className="mt-5 text-4xl font-semibold leading-tight text-white sm:text-6xl">
              AI News Credibility & Misinformation Detection Platform
            </h1>
            <p className="mt-6 max-w-2xl text-lg leading-8 text-slate-200">
              A full-stack machine learning platform for analyzing news text,
              comparing credibility classifiers, explaining model predictions,
              monitoring model behavior, and supporting structured human review.
            </p>
            <div className="mt-8 flex flex-col gap-3 sm:flex-row">
              <Link
                href="/analyze"
                className="inline-flex items-center justify-center rounded-md bg-white px-5 py-3 text-sm font-semibold text-slate-950 transition hover:bg-slate-100"
              >
                Analyze Article
              </Link>
              <Link
                href="/models"
                className="inline-flex items-center justify-center rounded-md border border-white/40 px-5 py-3 text-sm font-semibold text-white transition hover:bg-white/10"
              >
                Explore Models
              </Link>
            </div>
            <p className="mt-6 max-w-2xl text-sm leading-6 text-slate-300">
              Predictions are model outputs, confidence is model confidence,
              SHAP explains model behavior, evidence is reviewer-entered, and
              verified labels are human-entered. The platform does not
              independently prove factual truth.
            </p>
          </div>
        </div>
      </section>

      <section className="border-b border-slate-200 bg-white">
        <div className="mx-auto w-full max-w-7xl px-4 py-12 sm:px-6 lg:px-8">
          <div className="flex items-center gap-3">
            <span className="flex h-10 w-10 items-center justify-center rounded-lg bg-teal-50 text-signal">
              <SearchCheck aria-hidden="true" className="h-5 w-5" />
            </span>
            <div>
              <h2 className="text-2xl font-semibold text-ink">How the workflow fits together</h2>
              <p className="mt-1 text-sm leading-6 text-slate-600">
                Each step is explicit so prediction, explanation, review, evidence,
                and monitoring stay separate.
              </p>
            </div>
          </div>
          <div className="mt-7 flex flex-wrap items-center gap-3">
            {workflow.map((step, index) => (
              <div key={step} className="flex items-center gap-3">
                <span className="rounded-md border border-slate-200 bg-surface px-3 py-2 text-sm font-semibold text-slate-700">
                  {step}
                </span>
                {index < workflow.length - 1 ? <span className="text-slate-400">-&gt;</span> : null}
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="mx-auto w-full max-w-7xl px-4 py-14 sm:px-6 lg:px-8">
        <div className="grid gap-6 lg:grid-cols-[0.8fr_1.2fr]">
          <div>
            <h2 className="text-3xl font-semibold text-ink">Capability groups</h2>
            <p className="mt-4 text-base leading-7 text-slate-600">
              The platform brings together applied NLP, model evaluation, lifecycle
              workflows, and human review without positioning ML output as an
              automated truth engine.
            </p>
          </div>
          <div className="grid gap-4 sm:grid-cols-2">
            {capabilityGroups.map((group) => (
              <article key={group.title} className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
                <div className="flex items-center gap-3">
                  <span className="flex h-10 w-10 items-center justify-center rounded-lg bg-teal-50 text-signal">
                    <group.icon aria-hidden="true" className="h-5 w-5" />
                  </span>
                  <h3 className="text-lg font-semibold text-ink">{group.title}</h3>
                </div>
                <ul className="mt-4 grid gap-2 text-sm leading-6 text-slate-600">
                  {group.items.map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
              </article>
            ))}
          </div>
        </div>
      </section>

      <section className="border-y border-slate-200 bg-white">
        <div className="mx-auto grid w-full max-w-7xl gap-6 px-4 py-12 sm:px-6 lg:grid-cols-3 lg:px-8">
          <ResponsiblePanel
            icon={Gauge}
            title="Prediction"
            text="The model predicts likely credible or likely misinformation from learned text patterns and exposes confidence as a model signal."
          />
          <ResponsiblePanel
            icon={Eye}
            title="Explanation"
            text="SHAP and feature attribution show what influenced the model. Explanation is not factual evidence."
          />
          <ResponsiblePanel
            icon={ShieldCheck}
            title="Review"
            text="Verified labels, claims, and evidence assessments are entered by reviewers and remain separate from model outputs."
          />
        </div>
      </section>

      <section className="mx-auto flex w-full max-w-7xl flex-col gap-4 px-4 py-12 sm:px-6 md:flex-row md:items-center md:justify-between lg:px-8">
        <div>
          <h2 className="text-2xl font-semibold text-ink">Start with a trained model</h2>
          <p className="mt-2 text-sm leading-6 text-slate-600">
            Import a labeled dataset, train a baseline, promote a champion, then
            analyze and review saved articles.
          </p>
        </div>
        <div className="flex flex-col gap-3 sm:flex-row">
          <Link href="/data" className="inline-flex justify-center rounded-md border border-slate-300 px-4 py-2 text-sm font-semibold text-ink">
            Inspect Data
          </Link>
          <Link href="/models" className="inline-flex justify-center rounded-md bg-ink px-4 py-2 text-sm font-semibold text-white">
            Train Models
          </Link>
        </div>
      </section>
    </>
  );
}

function ResponsiblePanel({
  icon: Icon,
  title,
  text,
}: {
  icon: typeof Gauge;
  title: string;
  text: string;
}) {
  return (
    <article>
      <div className="flex items-center gap-3">
        <span className="flex h-10 w-10 items-center justify-center rounded-lg bg-teal-50 text-signal">
          <Icon aria-hidden="true" className="h-5 w-5" />
        </span>
        <h2 className="text-lg font-semibold text-ink">{title}</h2>
      </div>
      <p className="mt-3 text-sm leading-6 text-slate-600">{text}</p>
    </article>
  );
}
