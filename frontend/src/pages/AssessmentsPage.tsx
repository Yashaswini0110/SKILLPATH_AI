import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { fetchAssessments } from "../services/auth";
import { PageHeader } from "../components/common/PageHeader";
import { getErrorMessage } from "../services/api";

export function AssessmentsPage() {
  const query = useQuery({ queryKey: ["assessments"], queryFn: () => fetchAssessments() });
  const rows = query.data ?? [];

  return (
    <div className="space-y-6">
      <PageHeader title="Assess" />

      {query.isPending ? <p className="text-sm text-slate-500">Loading quizzes…</p> : null}
      {query.isError ? (
        <p className="text-sm text-red-600">{getErrorMessage(query.error, "Unable to load quizzes.")}</p>
      ) : null}

      <ul className="divide-y divide-slate-200 rounded-xl border border-slate-200 bg-white">
        {rows.map((row) => (
          <li key={row.id} className="flex flex-wrap items-center justify-between gap-3 px-4 py-3">
            <div>
              <p className="font-medium text-navy-900">{row.skill.canonical_name}</p>
              <p className="text-sm text-slate-500">
                {row.question_count} questions · pass {Math.round(row.pass_score * 100)}%
                {row.attempt_count
                  ? ` · last score ${Math.round((row.latest_percent ?? 0) * 100)}%`
                  : " · not started"}
              </p>
            </div>
            <Link
              to={`/assessments/${row.id}`}
              className="text-sm font-medium text-navy-800 underline-offset-2 hover:underline"
            >
              {row.attempt_count ? "Retake quiz" : "Take quiz"}
            </Link>
          </li>
        ))}
      </ul>
      {query.isSuccess && !rows.length ? (
        <p className="text-sm text-slate-500">No quizzes are seeded yet.</p>
      ) : null}
    </div>
  );
}
