import { BarChart3 } from "lucide-react";

import { EmptyState } from "@/components/EmptyState";
import { PageHeader } from "@/components/PageHeader";

export default function EvaluationPage() {
  return (
    <>
      <PageHeader
        eyebrow="Evaluation dashboard"
        title="Evaluation"
        description="A future dashboard for validation metrics, calibration checks, confusion matrices, and reproducible evaluation runs."
      />
      <div className="mx-auto w-full max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
        <EmptyState
          icon={BarChart3}
          title="Evaluation runs will appear here"
          description="No synthetic metrics are shown. This page will be connected after datasets, models, and evaluation pipelines exist."
        />
      </div>
    </>
  );
}

