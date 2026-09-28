import { useQuery } from "@tanstack/react-query";
import { fetchMentorMatches } from "../services/auth";
import { PageHeader } from "../components/common/PageHeader";
import { WhyButton } from "../components/common/WhyButton";
import { getErrorMessage } from "../services/api";
import type { MentorMatchItem } from "../types/api";

export function MentorsPage() {
  const query = useQuery({
    queryKey: ["mentor-matches"],
    queryFn: fetchMentorMatches,
    retry: false,
  });
  const data = query.data;

  return (
    <div className="space-y-6">
      <PageHeader title="Mentors" />

      {data ? (
        <p className="text-sm text-slate-500">Target: {data.target.title}</p>
      ) : null}

      {query.isPending ? <p className="text-sm text-slate-500">Matching…</p> : null}
      {query.isError ? (
        <p className="text-sm text-red-600">
          {getErrorMessage(
            query.error,
            "Select a target role or job description with open skill gaps first.",
          )}
        </p>
      ) : null}

      {query.isSuccess && !(data?.items.length) ? (
        <p className="text-sm text-slate-500">
          No catalog mentor covers your current top skill gaps.
        </p>
      ) : null}

      <ol className="space-y-4">
        {(data?.items ?? []).map((item) => (
          <MatchCard key={`${item.rank}-${item.mentor.id}`} item={item} />
        ))}
      </ol>
    </div>
  );
}

function MatchCard({ item }: { item: MentorMatchItem }) {
  const why = item.why;
  return (
    <li className="rounded-xl border border-slate-200 bg-white p-5">
      <div className="flex flex-wrap items-start justify-between gap-2">
        <div>
          <p className="font-medium text-navy-900">
            {item.rank}. {item.mentor.name}
          </p>
          <p className="text-sm text-slate-500">{item.mentor.title}</p>
        </div>
        <span className="rounded-full bg-slate-100 px-2 py-0.5 text-xs font-medium text-slate-700">
          {why.matched_gap_count} of {why.top_gap_count} gaps
        </span>
      </div>
      <WhyButton explanation={item.explanation} />
      <ul className="mt-3 flex flex-wrap gap-2">
        {why.matched_skills.map((skill) => (
          <li
            key={skill.id}
            className="rounded-lg bg-slate-50 px-3 py-1.5 text-xs text-slate-600"
          >
            {skill.canonical_name}
          </li>
        ))}
      </ul>
    </li>
  );
}
