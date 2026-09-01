import {
  BarChart3,
  BrainCircuit,
  ClipboardCheck,
  Database,
  Eye,
  Layers3,
  MonitorDot,
  ShieldCheck,
} from "lucide-react";

import { PageHeader } from "@/components/PageHeader";

const sections = [
  {
    title: "Problem",
    icon: ShieldCheck,
    text: "News credibility tools need more than a single prediction. They need traceable data, clear model outputs, human review, and visible limitations.",
  },
  {
    title: "Approach",
    icon: Layers3,
    text: "The platform separates ingestion, preprocessing, training, inference, explainability, review, evidence, and monitoring into testable backend services and focused frontend workspaces.",
  },
  {
    title: "ML Models",
    icon: BrainCircuit,
    text: "Logistic Regression and calibrated Linear SVM provide classical TF-IDF baselines. DistilBERT support adds a transformer path for contextual text representation.",
  },
  {
    title: "Explainability",
    icon: Eye,
    text: "SHAP and feature attribution show which learned text features influenced a model prediction. Explanation is not factual evidence.",
  },
  {
    title: "Monitoring",
    icon: MonitorDot,
    text: "Reference profiles, input drift, prediction drift, confidence distributions, and usage windows help answer whether model behavior has changed.",
  },
  {
    title: "Human Review",
    icon: ClipboardCheck,
    text: "Reviewers can assign explicit verified REAL/FAKE labels, enabling reviewed-production performance, calibration, and error analysis.",
  },
  {
    title: "Evidence Workflow",
    icon: Database,
    text: "Reviewers can manually identify claims and record evidence URLs with supports, contradicts, neutral, or unclear assessments. URLs are stored but not fetched.",
  },
  {
    title: "Limitations",
    icon: BarChart3,
    text: "The system is an ML analysis and evaluation platform, not an automated truth engine. It has no authentication, external fact-checking, source scoring, or automatic retraining.",
  },
];

const architecture = [
  "Next.js Frontend",
  "FastAPI REST API",
  "ML / Review / Monitoring Services",
  "PostgreSQL + Model Artifact Storage",
];

export default function AboutPage() {
  return (
    <>
      <PageHeader
        eyebrow="Technical overview"
        title="About News Credibility AI"
        description="A portfolio-ready full-stack ML platform for news credibility analysis, model evaluation, explainability, monitoring, and responsible human review."
      />
      <div className="mx-auto grid w-full max-w-7xl gap-6 px-4 py-8 sm:px-6 lg:px-8">
        <section className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
          <h2 className="text-xl font-semibold text-ink">Architecture</h2>
          <div className="mt-5 flex flex-wrap items-center gap-3">
            {architecture.map((step, index) => (
              <div key={step} className="flex items-center gap-3">
                <span className="rounded-md border border-slate-200 bg-surface px-3 py-2 text-sm font-semibold text-slate-700">
                  {step}
                </span>
                {index < architecture.length - 1 ? <span className="text-slate-400">-&gt;</span> : null}
              </div>
            ))}
          </div>
          <p className="mt-4 text-sm leading-6 text-slate-600">
            PostgreSQL stores structured records, labels, reviews, monitoring
            profiles, and analysis history. Model binaries live in controlled
            artifact storage on disk, not in the database.
          </p>
        </section>

        <section className="grid gap-4 md:grid-cols-2">
          {sections.map((section) => (
            <article key={section.title} className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
              <div className="flex items-center gap-3">
                <span className="flex h-10 w-10 items-center justify-center rounded-lg bg-teal-50 text-signal">
                  <section.icon aria-hidden="true" className="h-5 w-5" />
                </span>
                <h2 className="text-lg font-semibold text-ink">{section.title}</h2>
              </div>
              <p className="mt-4 text-sm leading-6 text-slate-600">{section.text}</p>
            </article>
          ))}
        </section>

        <section className="rounded-lg border border-amber-200 bg-amber-50 px-5 py-4 text-sm leading-6 text-amber-900">
          Most appropriate use today: development, education, portfolio
          demonstration, and controlled evaluation. Add authentication,
          authorization, distributed rate limiting, production observability,
          and deployment hardening before exposing sensitive workflows to
          untrusted users.
        </section>
      </div>
    </>
  );
}
