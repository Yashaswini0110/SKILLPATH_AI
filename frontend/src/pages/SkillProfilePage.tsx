import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { PageHeader } from "../components/common/PageHeader";
import { fetchSkillProfile } from "../services/auth";
import type { AggregatedSkill, ConfidenceLabel } from "../types/api";

const LABEL_STYLE: Record<ConfidenceLabel, string> = {
  HIGH: "bg-teal-100 text-teal-800",
  MEDIUM: "bg-amber-100 text-amber-800",
  LOW: "bg-slate-100 text-slate-700",
};

const SOURCE_LABEL: Record<string, string> = {
  SELF: "Self-declared",
  RESUME: "Resume",
  GITHUB: "GitHub",
  COURSE: "Course",
  ASSESSMENT: "Assessment",
  PROJECT: "Project",
  CERT: "Certification",
  WORK: "Work",
};

export function SkillProfilePage() {
  const profileQuery = useQuery({ queryKey: ["skill-profile"], queryFn: fetchSkillProfile });
  const profile = profileQuery.data;

  return (
    <div className="space-y-6">
      <PageHeader title="Skills" />

      <div className="grid gap-4 md:grid-cols-3">
        <StatCard label="Skills with evidence" value={String(profile?.skill_count ?? 0)} />
        <StatCard label="Conflicts" value={String(profile?.conflict_count ?? 0)} />
        <StatCard
          label="Self-declaration reliability"
          value={String(profile?.source_reliability.SELF ?? 0.3)}
        />
      </div>

      <ul className="space-y-3">
        {(profile?.skills ?? []).map((item) => (
          <SkillCard key={item.skill.id} item={item} />
        ))}
      </ul>
      {profile && !profile.skills.length ? (
        <p className="text-sm text-slate-500">
          Declare skills on your profile or upload a resume to build this estimate.
        </p>
      ) : null}
    </div>
  );
}

function SkillCard({ item }: { item: AggregatedSkill }) {
  return (
    <li className="rounded-xl border border-slate-200 bg-white p-5">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <p className="font-medium text-navy-900">{item.skill.canonical_name}</p>
        <div className="flex flex-wrap gap-2">
          <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${LABEL_STYLE[item.confidence_label]}`}>
            {item.confidence_label.toLowerCase()} confidence
          </span>
          {item.inferred_only ? (
            <span className="rounded-full bg-amber-100 px-2 py-0.5 text-xs font-medium text-amber-800">
              inferred
            </span>
          ) : null}
          {item.conflict ? (
            <span className="rounded-full bg-red-100 px-2 py-0.5 text-xs font-medium text-red-800">
              conflict
            </span>
          ) : null}
        </div>
      </div>
      <p className="mt-1 text-sm text-slate-500">
        Estimated level {item.current_level}/5 · confidence {item.confidence}
      </p>
      {item.recommend_assessment ? (
        <p className="mt-2 text-sm text-amber-800">
          Conflict.{" "}
          <Link to="/assessments" className="font-medium underline-offset-2 hover:underline">
            Quiz
          </Link>
        </p>
      ) : (
        <p className="mt-2">
          <Link
            to="/assessments"
            className="text-sm font-medium text-navy-800 underline-offset-2 hover:underline"
          >
            Quiz
          </Link>
        </p>
      )}
      <ul className="mt-3 flex flex-wrap gap-2">
        {item.evidence.map((row, index) => (
          <li
            key={row.id ?? `${row.source_type}-${index}`}
            className="rounded-lg bg-slate-50 px-3 py-1.5 text-xs text-slate-600"
          >
            {SOURCE_LABEL[row.source_type] ?? row.source_type}
            {" · "}
            level {row.extracted_level}
            {row.inferred ? " · inferred" : ""}
          </li>
        ))}
      </ul>
    </li>
  );
}

function StatCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-5">
      <p className="text-xs uppercase tracking-wide text-slate-500">{label}</p>
      <p className="mt-2 text-xl font-semibold text-navy-900">{value}</p>
    </div>
  );
}
