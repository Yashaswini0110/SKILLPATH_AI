import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { fetchRecommendations } from "../services/auth";
import { getErrorMessage } from "../services/api";
import { PageHeader } from "../components/common/PageHeader";
import { WhyButton } from "../components/common/WhyButton";
import { inputClass } from "../components/common/AuthCard";
import type { RecMethod, RecommendationItem } from "../types/api";

type ResourceTab = "courses" | "projects" | "mentors";

export function RecommendationsPage() {
  const [tab, setTab] = useState<ResourceTab>("courses");
  const [method, setMethod] = useState<RecMethod>("HYBRID");
  const query = useQuery({
    queryKey: ["recommendations", tab, method],
    queryFn: () => fetchRecommendations({ resource: tab, method }),
    retry: false,
  });
  const data = query.data;

  return (
    <div className="space-y-6">
      <PageHeader title="Recommendations" />

      <section className="rounded-xl border border-slate-200 bg-white p-6">
        <div className="grid gap-4 md:grid-cols-2">
          <label className="text-sm text-slate-600">
            Method
            <select
              className={`${inputClass} mt-1`}
              value={method}
              onChange={(event) => setMethod(event.target.value as RecMethod)}
            >
              <option value="HYBRID">Hybrid</option>
              <option value="CONTENT">Content-based</option>
              <option value="POPULARITY">Popularity</option>
              <option value="SEMANTIC">Semantic</option>
              <option value="KG">Knowledge graph</option>
            </select>
          </label>
          <div className="flex flex-wrap items-end gap-2" role="tablist" aria-label="Resource type">
            <TabButton current={tab} id="courses" label="Courses" onSelect={setTab} />
            <TabButton current={tab} id="projects" label="Projects" onSelect={setTab} />
            <TabButton current={tab} id="mentors" label="Mentors" onSelect={setTab} />
          </div>
        </div>
        {data ? (
          <p className="mt-4 text-sm text-slate-500">Target: {data.target.title}</p>
        ) : null}
      </section>

      {query.isPending ? <p className="text-sm text-slate-500">Ranking…</p> : null}
      {query.isError ? (
        <p className="text-sm text-red-600" role="alert">
          {getErrorMessage(
            query.error,
            "Select a target role or job description with open skill gaps first.",
          )}
        </p>
      ) : null}

      {query.isSuccess && !data?.items.length ? (
        <p className="text-sm text-slate-500">
          No catalog resources teach your current top skill gaps.
        </p>
      ) : null}

      <ol className="space-y-3">
        {(data?.items ?? []).map((item) => (
          <RankCard key={`${item.rank}-${titleOf(item)}`} item={item} />
        ))}
      </ol>
    </div>
  );
}

function RankCard({ item }: { item: RecommendationItem }) {
  const title = titleOf(item);
  return (
    <li className="rounded-xl border border-slate-200 bg-white p-5">
      <div className="flex flex-wrap items-start justify-between gap-2">
        <p className="font-medium text-navy-900">
          {item.rank}. {title}
        </p>
        <span className="text-xs text-slate-500">{metaLine(item)}</span>
      </div>
      <WhyButton explanation={item.explanation} />
      <ul className="mt-3 flex flex-wrap gap-2">
        {item.matched_skills.map((row) => (
          <li key={row.skill.id} className="text-xs text-slate-600">
            {row.skill.canonical_name}
            {row.priority ? ` · ${row.priority.toLowerCase()}` : ""}
            {row.gap != null ? ` · gap ${row.gap}` : ""}
          </li>
        ))}
      </ul>
    </li>
  );
}

function TabButton({
  current,
  id,
  label,
  onSelect,
}: {
  current: ResourceTab;
  id: ResourceTab;
  label: string;
  onSelect: (tab: ResourceTab) => void;
}) {
  const active = current === id;
  return (
    <button
      type="button"
      role="tab"
      aria-selected={active}
      onClick={() => onSelect(id)}
      className={[
        "rounded-lg px-3 py-1.5 text-sm font-medium focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-navy-700",
        active ? "bg-navy-800 text-white" : "border border-slate-300 text-slate-700",
      ].join(" ")}
    >
      {label}
    </button>
  );
}

function titleOf(item: RecommendationItem): string {
  return item.course?.title ?? item.project?.title ?? item.mentor?.name ?? "Resource";
}

function metaLine(item: RecommendationItem): string {
  if (item.course) {
    return `${item.course.duration_hours}h · difficulty ${item.course.difficulty}/5`;
  }
  if (item.project) {
    return `${item.project.duration_hours}h · difficulty ${item.project.difficulty}/5`;
  }
  if (item.mentor) {
    return `${item.mentor.available_hours_per_month}h / month`;
  }
  return `score ${item.score}`;
}

