import Link from "next/link";
import { ArrowLeft, FileText } from "lucide-react";

import { EmptyState } from "@/components/EmptyState";
import { EvidenceWorkspaceClient } from "@/components/EvidenceWorkspaceClient";
import { PageHeader } from "@/components/PageHeader";
import {
  AnalysisEvidenceSummary,
  AnalysisHistoryDetail,
  ClaimsList,
  fetchFromApi,
} from "@/lib/api";

export const dynamic = "force-dynamic";

type EvidencePageProps = {
  params: Promise<{ analysisId: string }>;
};

async function loadEvidenceWorkspace(analysisId: string) {
  try {
    const [analysis, claims, summary] = await Promise.all([
      fetchFromApi<AnalysisHistoryDetail>(`/api/v1/history/${analysisId}`),
      fetchFromApi<ClaimsList>(`/api/v1/history/${analysisId}/claims?limit=100&offset=0`),
      fetchFromApi<AnalysisEvidenceSummary>(`/api/v1/history/${analysisId}/evidence-summary`),
    ]);
    return { analysis, claims, summary };
  } catch {
    return null;
  }
}

export default async function EvidencePage({ params }: EvidencePageProps) {
  const { analysisId } = await params;
  const data = await loadEvidenceWorkspace(analysisId);

  if (!data) {
    return (
      <>
        <PageHeader
          eyebrow="Evidence workspace"
          title="Claims and evidence"
          description="This saved analysis could not be loaded."
        />
        <div className="mx-auto w-full max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
          <EmptyState
            icon={FileText}
            title="Evidence workspace unavailable"
            description="The saved analysis may have been deleted, or the evidence API may be unavailable."
          />
        </div>
      </>
    );
  }

  return (
    <>
      <PageHeader
        eyebrow="Manual evidence review"
        title={data.analysis.title || "Untitled analysis"}
        description="Identify claims manually, record references you found, and assess how each reference relates to each claim."
      />
      <div className="mx-auto grid w-full max-w-7xl gap-6 px-4 py-8 sm:px-6 lg:px-8">
        <Link href={`/history/${analysisId}`} className="inline-flex w-fit items-center gap-2 text-sm font-semibold text-ink">
          <ArrowLeft aria-hidden="true" className="h-4 w-4" />
          Back to saved analysis
        </Link>
        <section className="rounded-lg border border-amber-200 bg-amber-50 px-5 py-4 text-sm leading-6 text-amber-900">
          Evidence URLs and metadata are manually entered references. The backend stores them only; it does not fetch pages, inspect metadata, classify evidence, or determine the verified label.
        </section>
        <EvidenceWorkspaceClient analysis={data.analysis} claims={data.claims.items} summary={data.summary} />
      </div>
    </>
  );
}
