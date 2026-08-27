type PageHeaderProps = {
  eyebrow?: string;
  title: string;
  description: string;
};

export function PageHeader({ eyebrow, title, description }: PageHeaderProps) {
  return (
    <header className="border-b border-slate-200 bg-white">
      <div className="mx-auto flex w-full max-w-7xl flex-col gap-4 px-4 py-10 sm:px-6 lg:px-8">
        {eyebrow ? (
          <p className="text-sm font-semibold uppercase tracking-wide text-signal">
            {eyebrow}
          </p>
        ) : null}
        <div className="max-w-3xl">
          <h1 className="text-3xl font-semibold text-ink sm:text-4xl">{title}</h1>
          <p className="mt-4 text-base leading-7 text-slate-600">{description}</p>
        </div>
      </div>
    </header>
  );
}

