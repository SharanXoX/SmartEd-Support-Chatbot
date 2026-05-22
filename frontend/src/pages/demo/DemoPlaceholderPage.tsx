type Props = {
  title: string;
  description: string;
  hint?: string;
};

export default function DemoPlaceholderPage({ title, description, hint }: Props) {
  return (
    <div className="mx-auto max-w-3xl rounded-2xl border border-dashed border-slate-300 bg-white p-8 dark:border-slate-700 dark:bg-slate-900">
      <h2 className="text-xl font-semibold text-slate-900 dark:text-slate-50">{title}</h2>
      <p className="mt-2 text-sm leading-relaxed text-slate-600 dark:text-slate-300">{description}</p>
      {hint ? (
        <p className="mt-4 rounded-lg bg-brand-600/5 px-3 py-2 text-xs text-brand-800 dark:text-brand-200">
          {hint}
        </p>
      ) : null}
    </div>
  );
}
