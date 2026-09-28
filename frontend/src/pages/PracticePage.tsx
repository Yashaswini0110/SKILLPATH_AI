import { useQuery } from "@tanstack/react-query";
import { fetchPracticePairs } from "../services/auth";
import { PageHeader } from "../components/common/PageHeader";
import { WhyButton } from "../components/common/WhyButton";
import { getErrorMessage } from "../services/api";
import type { PracticePair } from "../types/api";

export function PracticePage() {
  const query = useQuery({
    queryKey: ["practice-pairs"],
    queryFn: fetchPracticePairs,
    retry: false,
  });
  const data = query.data;

  return (
    <div className="space-y-6">
      <PageHeader title="Practice" />

      {data ? (
        <p className="text-sm text-slate-500">
          Target {data.target.title} · {data.items.length}{" "}
          {data.items.length === 1 ? "pair" : "pairs"}
        </p>
      ) : null}

      {query.isPending ? <p className="text-sm text-slate-500">Pairing…</p> : null}
      {query.isError ? (
        <p className="text-sm text-red-600">
          {getErrorMessage(
            query.error,
            "Select a target role or job description with major skill gaps first.",
          )}
        </p>
      ) : null}

      {query.isSuccess && !(data?.items.length) ? (
        <p className="text-sm text-slate-500">
          No catalog course and project both teach a current major gap.
        </p>
      ) : null}

      <ol className="space-y-4">
        {(data?.items ?? []).map((item) => (
          <PairCard key={`${item.rank}-${item.skill.id}`} item={item} />
        ))}
      </ol>
    </div>
  );
}

function PairCard({ item }: { item: PracticePair }) {
  return (
    <li className="rounded-xl border border-slate-200 bg-white p-5">
      <div className="flex flex-wrap items-start justify-between gap-2">
        <p className="font-medium text-navy-900">
          {item.rank}. {item.skill.canonical_name}
        </p>
        <span className="rounded-full bg-slate-100 px-2 py-0.5 text-xs font-medium text-slate-700">
          {item.priority.toLowerCase()} · score {item.score}
        </span>
      </div>
      <WhyButton explanation={item.explanation} />
      <div className="mt-4 grid gap-3 md:grid-cols-3">
        <Step
          label="Skill"
          title={item.skill.canonical_name}
          detail={`current ${fmt(item.current_level)} → required ${fmt(item.required_level)}`}
        />
        <Step
          label="Course"
          title={item.course.title}
          detail={`${item.course.duration_hours}h · difficulty ${item.course.difficulty}/5`}
        />
        <Step
          label="Project"
          title={item.project.title}
          detail={`${item.project.duration_hours}h · ${item.project.technologies.join(", ") || "practice"}`}
        />
      </div>
    </li>
  );
}

function Step({
  label,
  title,
  detail,
}: {
  label: string;
  title: string;
  detail: string;
}) {
  return (
    <div className="rounded-lg bg-slate-50 p-3">
      <p className="text-xs uppercase tracking-wide text-slate-500">{label}</p>
      <p className="mt-1 text-sm font-medium text-navy-900">{title}</p>
      <p className="mt-1 text-xs text-slate-500">{detail}</p>
    </div>
  );
}

function fmt(value: number | string): string {
  return String(value);
}
