export function PageHeader({ title, note }: { title: string; note?: string }) {
  return (
    <div>
      <h1 className="text-2xl font-semibold text-navy-900">{title}</h1>
      {note ? <p className="mt-1 text-sm text-slate-500">{note}</p> : null}
    </div>
  );
}
