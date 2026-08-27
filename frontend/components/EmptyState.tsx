import type { LucideIcon } from "lucide-react";

type EmptyStateProps = {
  icon: LucideIcon;
  title: string;
  description: string;
};

export function EmptyState({ icon: Icon, title, description }: EmptyStateProps) {
  return (
    <section className="rounded-lg border border-dashed border-slate-300 bg-white px-6 py-14 text-center shadow-sm">
      <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-lg bg-teal-50 text-signal">
        <Icon aria-hidden="true" className="h-6 w-6" />
      </div>
      <h2 className="mt-5 text-xl font-semibold text-ink">{title}</h2>
      <p className="mx-auto mt-3 max-w-2xl text-sm leading-6 text-slate-600">
        {description}
      </p>
    </section>
  );
}

