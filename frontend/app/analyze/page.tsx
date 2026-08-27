import { FileText, LockKeyhole, SendHorizontal } from "lucide-react";

import { PageHeader } from "@/components/PageHeader";

export default function AnalyzePage() {
  return (
    <>
      <PageHeader
        eyebrow="Analysis workspace"
        title="Article and headline analysis"
        description="This workspace is reserved for a future NLP and model inference workflow. The input interface is present so the product shell can be designed without introducing prediction behavior."
      />
      <div className="mx-auto grid w-full max-w-7xl gap-6 px-4 py-8 sm:px-6 lg:grid-cols-[1fr_320px] lg:px-8">
        <section className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
          <div className="flex items-center gap-3">
            <span className="flex h-10 w-10 items-center justify-center rounded-lg bg-teal-50 text-signal">
              <FileText aria-hidden="true" className="h-5 w-5" />
            </span>
            <div>
              <h2 className="text-lg font-semibold text-ink">Future article input</h2>
              <p className="text-sm text-slate-500">Prediction services are not connected yet.</p>
            </div>
          </div>

          <div className="mt-6 grid gap-4">
            <label className="grid gap-2">
              <span className="text-sm font-medium text-slate-700">Headline or article URL</span>
              <input
                disabled
                placeholder="Input will be enabled when the analysis API is implemented"
                className="h-11 rounded-md border border-slate-200 bg-slate-50 px-3 text-sm text-slate-500 outline-none"
              />
            </label>
            <label className="grid gap-2">
              <span className="text-sm font-medium text-slate-700">Article text</span>
              <textarea
                disabled
                rows={10}
                placeholder="Future prompts will connect NLP preprocessing and model inference here."
                className="resize-none rounded-md border border-slate-200 bg-slate-50 px-3 py-3 text-sm text-slate-500 outline-none"
              />
            </label>
            <button
              type="button"
              disabled
              className="inline-flex w-full items-center justify-center gap-2 rounded-md bg-slate-200 px-5 py-3 text-sm font-semibold text-slate-500 sm:w-fit"
            >
              <SendHorizontal aria-hidden="true" className="h-4 w-4" />
              Analyze article
            </button>
          </div>
        </section>

        <aside className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
          <div className="flex items-center gap-3">
            <span className="flex h-10 w-10 items-center justify-center rounded-lg bg-amber-50 text-review">
              <LockKeyhole aria-hidden="true" className="h-5 w-5" />
            </span>
            <h2 className="text-lg font-semibold text-ink">Not active yet</h2>
          </div>
          <p className="mt-4 text-sm leading-6 text-slate-600">
            This page intentionally avoids model outputs until preprocessing,
            inference, confidence scoring, and explainability contracts are built.
          </p>
        </aside>
      </div>
    </>
  );
}

