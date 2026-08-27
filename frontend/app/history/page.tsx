import { History } from "lucide-react";

import { EmptyState } from "@/components/EmptyState";
import { PageHeader } from "@/components/PageHeader";

export default function HistoryPage() {
  return (
    <>
      <PageHeader
        eyebrow="Prediction history"
        title="History"
        description="A future audit trail for submitted articles, model versions, confidence estimates, and explanation references."
      />
      <div className="mx-auto w-full max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
        <EmptyState
          icon={History}
          title="No prediction history yet"
          description="History will become available after the prediction API and persistence model are intentionally designed."
        />
      </div>
    </>
  );
}

