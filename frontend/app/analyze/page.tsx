import { BrainCircuit } from "lucide-react";
import { AnalyzeClient } from "@/components/AnalyzeClient";
import { EmptyState } from "@/components/EmptyState";
import { PageHeader } from "@/components/PageHeader";
import { MLTrainingRun, PaginatedResponse, fetchFromApi } from "@/lib/api";

export const dynamic = "force-dynamic";

async function loadCompletedModels() {
  try {
    const response = await fetchFromApi<PaginatedResponse<MLTrainingRun>>(
      "/api/v1/ml/training-runs?status=completed&limit=50&offset=0",
    );
    return response.items;
  } catch {
    return null;
  }
}

export default async function AnalyzePage() {
  const models = await loadCompletedModels();

  return (
    <>
      <PageHeader
        eyebrow="Analysis workspace"
        title="Article and headline analysis"
        description="Run inference with completed classical baseline models. Outputs are statistical model predictions, not independent fact verification."
      />
      {models === null ? (
        <div className="mx-auto w-full max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
          <section className="rounded-lg border border-amber-200 bg-amber-50 px-5 py-4 text-sm leading-6 text-amber-900">
            Backend inference APIs are not reachable right now.
          </section>
        </div>
      ) : models.length ? (
        <AnalyzeClient models={models} />
      ) : (
        <div className="mx-auto w-full max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
          <EmptyState
            icon={BrainCircuit}
            title="No completed models available"
            description="Import a labeled dataset and train a classical baseline before running model-based inference."
          />
        </div>
      )}
    </>
  );
}
