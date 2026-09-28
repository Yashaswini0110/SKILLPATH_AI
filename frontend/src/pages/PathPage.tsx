import { useState } from "react";
import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { fetchLearningPath } from "../services/auth";
import { PageHeader } from "../components/common/PageHeader";
import { WhyButton } from "../components/common/WhyButton";
import { getErrorMessage } from "../services/api";
import type { LearningPath, LearningPathStep, PathStage } from "../types/api";

const STAGE_LABELS: Record<string, string> = {
  FOUNDATION: "Learn first",
  CORE: "Core",
  ADVANCED: "Later",
};

export function PathPage() {
  const [showFullList, setShowFullList] = useState(false);
  const method = showFullList ? "TOPOLOGICAL" : "ORTOOLS";
  const query = useQuery({
    queryKey: ["learning-path", method],
    queryFn: () => fetchLearningPath(method),
    retry: false,
  });
  const data = query.data;
  const steps = data?.steps ?? [];
  const groups = groupSteps(steps);

  return (
    <div className="space-y-6">
      <PageHeader title="Path" />

      {data ? <PlanSummary data={data} showingFullList={showFullList} /> : null}

      {data ? (
        <button
          type="button"
          onClick={() => setShowFullList((value) => !value)}
          className="text-sm font-medium text-navy-800 underline-offset-2 hover:underline"
        >
          {showFullList ? "Fit to hours" : "Show all skills"}
        </button>
      ) : null}

      {query.isPending ? <p className="text-sm text-slate-500">Building your path…</p> : null}
      {query.isError ? (
        <p className="text-sm text-red-600">
          {getErrorMessage(
            query.error,
            "Select a target role or job description with open skill gaps first.",
          )}
        </p>
      ) : null}

      {query.isSuccess && !steps.length ? (
        <p className="text-sm text-slate-500">
          Nothing fits in your current weekly hours. Increase hours on Profile, or
          pick a longer deadline.
        </p>
      ) : null}

      <div className="space-y-8">
        {groups.map((group) => (
          <section key={`${group.stage}-${group.steps[0]?.position ?? 0}`}>
            <h2 className="text-sm font-semibold uppercase tracking-wide text-navy-800">
              {STAGE_LABELS[group.stage] ?? group.stage}
            </h2>
            <ol className="relative ml-2 mt-4 border-l border-slate-200">
              {group.steps.map((step) => (
                <StepRow key={`${step.position}-${step.skill.id}`} step={step} />
              ))}
            </ol>
          </section>
        ))}
      </div>
    </div>
  );
}

function PlanSummary({
  data,
  showingFullList,
}: {
  data: LearningPath;
  showingFullList: boolean;
}) {
  const full = data.comparison.find((row) => row.method === "TOPOLOGICAL");
  const fullHours = full?.total_hours ?? data.total_hours;
  const overBudget = fullHours > data.capacity_hours;
  const weeks =
    data.hours_per_week > 0
      ? Math.ceil(data.total_hours / data.hours_per_week)
      : data.estimated_weeks;

  return (
    <div className="rounded-xl border border-slate-200 bg-white p-4 text-sm text-slate-600">
      <p>
        <span className="font-medium text-navy-900">{data.target.title}</span>
        {" · "}
        {data.total_hours}h / {data.capacity_hours}h
        {weeks ? ` · ${weeks} wk` : ""}
        {showingFullList && overBudget ? ` · full list ${fullHours}h` : ""}
      </p>
    </div>
  );
}

function StepRow({ step }: { step: LearningPathStep }) {
  const week =
    step.week_start === step.week_end
      ? `week ${step.week_start}`
      : `weeks ${step.week_start}–${step.week_end}`;
  return (
    <li className="relative mb-2 pl-8">
      <span className="absolute -left-[13px] flex h-6 w-6 items-center justify-center rounded-full border border-slate-300 bg-white text-xs font-medium text-navy-900">
        {step.position}
      </span>
      <div className="pb-6">
        <div className="flex flex-wrap items-baseline gap-2">
          <p className="font-medium text-navy-900">{step.skill.canonical_name}</p>
          <span className="text-xs text-slate-500">
            {step.kind === "REFRESHER" ? "Review · " : ""}
            {statusLabel(step.status)} · difficulty {step.difficulty}/5 · {week} ·{" "}
            {step.duration_hours}h
          </span>
        </div>
        <WhyButton explanation={step.explanation} />
        {step.course || step.project ? (
          <p className="mt-2 text-sm text-slate-500">
            {step.course?.title}
            {step.course && step.project ? " → " : ""}
            {step.project?.title}
          </p>
        ) : null}
        {step.assessment_id ? (
          <p className="mt-2">
            <Link
              to={`/assessments/${step.assessment_id}`}
              className="text-sm font-medium text-navy-800 underline-offset-2 hover:underline"
            >
              {step.status === "COMPLETED" ? "Retake quiz" : "Take quiz"}
            </Link>
          </p>
        ) : null}
      </div>
    </li>
  );
}

function groupSteps(steps: LearningPathStep[]): { stage: PathStage; steps: LearningPathStep[] }[] {
  const groups: { stage: PathStage; steps: LearningPathStep[] }[] = [];
  for (const step of steps) {
    const stage = step.stage || (step.kind === "FOUNDATION" ? "FOUNDATION" : "CORE");
    const current = groups[groups.length - 1];
    if (!current || current.stage !== stage) {
      groups.push({ stage, steps: [step] });
    } else {
      current.steps.push(step);
    }
  }
  return groups;
}

function statusLabel(status: string): string {
  if (status === "NOT_STARTED" || !status) {
    return "Not started";
  }
  if (status === "COMPLETED") {
    return "Completed";
  }
  if (status === "IN_PROGRESS") {
    return "In progress";
  }
  return status.replaceAll("_", " ").toLowerCase();
}
