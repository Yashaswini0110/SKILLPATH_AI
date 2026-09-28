import type { FormEvent, ReactNode } from "react";

interface Props {
  title: string;
  subtitle: string;
  children: ReactNode;
  onSubmit: (event: FormEvent<HTMLFormElement>) => void;
  submitLabel: string;
  footer: ReactNode;
  error?: string | null;
  pending?: boolean;
}

export function AuthCard({
  title,
  subtitle,
  children,
  onSubmit,
  submitLabel,
  footer,
  error,
  pending,
}: Props) {
  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-100 px-4">
      <div className="w-full max-w-md rounded-2xl border border-slate-200 bg-white p-8 shadow-sm">
        <p className="text-xs font-semibold uppercase tracking-[0.2em] text-teal-600">
          SkillPath AI
        </p>
        <h1 className="mt-2 text-2xl font-semibold text-navy-900">{title}</h1>
        <p className="mt-1 text-sm text-slate-500">{subtitle}</p>
        <form className="mt-6 space-y-4" onSubmit={onSubmit}>
          {children}
          {error ? (
            <p className="text-sm text-red-600" role="alert">
              {error}
            </p>
          ) : null}
          <button
            type="submit"
            disabled={pending}
            className="w-full rounded-lg bg-navy-800 px-4 py-2.5 text-sm font-medium text-white hover:bg-navy-700 disabled:opacity-60"
          >
            {pending ? "Please wait..." : submitLabel}
          </button>
        </form>
        <div className="mt-4 text-center text-sm text-slate-600">{footer}</div>
      </div>
    </div>
  );
}

export function Field({
  label,
  children,
}: {
  label: string;
  children: ReactNode;
}) {
  return (
    <label className="block">
      <span className="mb-1 block text-sm font-medium text-slate-700">{label}</span>
      {children}
    </label>
  );
}

export const inputClass =
  "w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-teal-500 focus:ring-2 focus:ring-teal-100";
