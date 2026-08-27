import { GitCompare } from "lucide-react";

import { EmptyState } from "@/components/EmptyState";
import { PageHeader } from "@/components/PageHeader";

export default function ModelsPage() {
  return (
    <>
      <PageHeader
        eyebrow="Model comparison"
        title="Models"
        description="A future comparison surface for classical ML baselines, transformer classifiers, model versions, and calibration behavior."
      />
      <div className="mx-auto w-full max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
        <EmptyState
          icon={GitCompare}
          title="No models registered yet"
          description="Model metadata, comparison metrics, and artifact references will be added after the ML service contracts are implemented."
        />
      </div>
    </>
  );
}

