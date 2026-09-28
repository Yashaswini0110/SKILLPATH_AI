import { Link } from "react-router-dom";
import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { PageHeader } from "../components/common/PageHeader";
import { fetchTwin } from "../services/auth";
import { getErrorMessage } from "../services/api";
import type { TwinSkill, TwinTrend } from "../types/api";

const SOURCE_LABEL: Record<string, string> = {
  SELF: "Self",
  RESUME: "Resume",
  ASSESSMENT: "Quiz",
  GITHUB: "GitHub",
  COURSE: "Course",
  PROJECT: "Project",
  CERT: "Cert",
  WORK: "Work",
};

const TREND_LABEL: Record<TwinTrend, string> = {
  IMPROVING: "Improving",
  STABLE: "Stable",
  DECLINING: "Declining",
  INSUFFICIENT_DATA: "Not enough data",
};

type Filter = "all" | "open" | "conflict";

export function TwinPage() {
  const [filter, setFilter] = useState<Filter>("all");
  const twinQuery = useQuery({
    queryKey: ["twin"],
    queryFn: () => fetchTwin(),
    retry: false,
  });
  const data = twinQuery.data;
  const error = twinQuery.error
    ? getErrorMessage(twinQuery.error, "Unable to load the skill twin.")
    : null;

  const rows = useMemo(() => {
    const skills = data?.skills ?? [];
    if (filter === "open") {
      return skills.filter((item) => item.priority && item.priority !== "NONE");
    }
    if (filter === "conflict") {
      return skills.filter((item) => item.conflict);
    }
    return skills;
  }, [data?.skills, filter]);

  return (
    <div className="space-y-6">
      <PageHeader title="Twin" />

      {error ? <p className="text-sm text-red-600">{error}</p> : null}
      {twinQuery.isFetching ? (
        <p className="text-sm text-slate-500">Loading stored competency state…</p>
      ) : null}

      {data ? (
        <>
          <p className="text-sm text-slate-600">
            {data.target.title} · {data.open_gap_count} gaps
            {data.conflict_count ? ` · ${data.conflict_count} conflicts` : ""}
          </p>

          <label className="block text-sm text-slate-600">
            Show
            <select
              className="ml-2 rounded-md border border-slate-300 px-2 py-1 text-sm"
              value={filter}
              onChange={(event) => setFilter(event.target.value as Filter)}
            >
              <option value="all">All skills</option>
              <option value="open">Open gaps</option>
              <option value="conflict">Conflicts</option>
            </select>
          </label>

          <section className="overflow-x-auto rounded-xl border border-slate-200 bg-white p-6">
            <table className="min-w-full text-left text-sm">
              <thead>
                <tr className="border-b border-slate-200 text-xs uppercase tracking-wide text-slate-500">
                  <th className="py-2 pr-4 font-medium">Skill</th>
                  <th className="py-2 pr-4 font-medium">Current</th>
                  <th className="py-2 pr-4 font-medium">Required</th>
                  <th className="py-2 pr-4 font-medium">Gap</th>
                  <th className="py-2 pr-4 font-medium">Confidence</th>
                  <th className="py-2 pr-4 font-medium">Evidence</th>
                  <th className="py-2 font-medium">Trend</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((item) => (
                  <TwinRow key={item.skill.id} item={item} />
                ))}
              </tbody>
            </table>
            {rows.length === 0 ? (
              <p className="mt-4 text-sm text-slate-500">No skills match this filter.</p>
            ) : null}
          </section>
        </>
      ) : null}
    </div>
  );
}

function TwinRow({ item }: { item: TwinSkill }) {
  const present = item.evidence_sources.filter((source) => source.present);
  const history = item.history
    .map((point) => `${SOURCE_LABEL[point.source_type] ?? point.source_type} ${Number(point.level).toFixed(1)}`)
    .join(" → ");

  return (
    <tr className="border-b border-slate-100 align-top">
      <td className="py-3 pr-4 font-medium text-navy-900">
        {item.skill.canonical_name}
        {item.priority && item.priority !== "NONE" ? (
          <span className="block text-xs font-normal text-slate-400">
            {item.priority.toLowerCase()}
            {item.requirement ? ` · ${item.requirement.toLowerCase()}` : ""}
          </span>
        ) : null}
        {item.conflict ? (
          <span className="block text-xs font-normal text-red-600">conflict</span>
        ) : null}
      </td>
      <td className="py-3 pr-4 text-slate-600">{Number(item.current_level).toFixed(1)}</td>
      <td className="py-3 pr-4 text-slate-600">
        {item.required_level == null ? "—" : Number(item.required_level).toFixed(1)}
      </td>
      <td className="py-3 pr-4 text-slate-600">
        {item.gap_basic == null ? "—" : Number(item.gap_basic).toFixed(1)}
      </td>
      <td className="py-3 pr-4 text-slate-600">
        {item.confidence_label.toLowerCase()}
        <span className="block text-xs text-slate-400">
          {Number(item.confidence).toFixed(2)}
        </span>
      </td>
      <td className="py-3 pr-4 text-slate-600">
        {present.length
          ? present.map((source) => SOURCE_LABEL[source.source_type] ?? source.source_type).join(", ")
          : "None"}
        {item.conflict || item.recommend_assessment ? (
          <Link to="/assessments" className="mt-1 block text-xs text-teal-700 hover:underline">
            Take a quiz
          </Link>
        ) : null}
      </td>
      <td className="py-3 text-slate-600">
        {TREND_LABEL[item.trend]}
        {history ? <span className="block text-xs text-slate-400">{history}</span> : null}
      </td>
    </tr>
  );
}
