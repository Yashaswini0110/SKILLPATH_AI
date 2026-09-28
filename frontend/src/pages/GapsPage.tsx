import { useQuery } from "@tanstack/react-query";
import { useEffect, useMemo, useState } from "react";
import { useSearchParams } from "react-router-dom";
import {
  fetchGapAnalysis,
  fetchJobDescriptions,
  fetchProfile,
  fetchRoles,
} from "../services/auth";
import { getErrorMessage } from "../services/api";
import { PageHeader } from "../components/common/PageHeader";
import { inputClass } from "../components/common/AuthCard";
import { GraphPanel } from "./GraphPage";
import type { GapItem, GapPriority } from "../types/api";

const PRIORITY_STYLE: Record<GapPriority, string> = {
  CRITICAL: "bg-red-100 text-red-800",
  HIGH: "bg-orange-100 text-orange-800",
  MEDIUM: "bg-amber-100 text-amber-800",
  LOW: "bg-slate-100 text-slate-700",
  NONE: "bg-teal-100 text-teal-800",
};

type TargetMode = "role" | "jd";
type Panel = "gaps" | "graph";

export function GapsPage() {
  const [params, setParams] = useSearchParams();
  const tab: Panel = params.get("tab") === "graph" ? "graph" : "gaps";

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <PageHeader title="Gaps" />
        <div className="flex flex-wrap gap-2" role="tablist" aria-label="Gaps and graph">
          <TabButton
            current={tab}
            id="gaps"
            label="Gaps"
            onSelect={(next) => setParams(next === "graph" ? { tab: "graph" } : {}, { replace: true })}
          />
          <TabButton
            current={tab}
            id="graph"
            label="Graph"
            onSelect={(next) => setParams(next === "graph" ? { tab: "graph" } : {}, { replace: true })}
          />
        </div>
      </div>
      {tab === "graph" ? <GraphPanel /> : <GapsPanel />}
    </div>
  );
}

function TabButton({
  current,
  id,
  label,
  onSelect,
}: {
  current: Panel;
  id: Panel;
  label: string;
  onSelect: (tab: Panel) => void;
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

function GapsPanel() {
  const profileQuery = useQuery({ queryKey: ["profile"], queryFn: fetchProfile });
  const rolesQuery = useQuery({ queryKey: ["roles"], queryFn: fetchRoles });
  const jdListQuery = useQuery({ queryKey: ["job-descriptions"], queryFn: fetchJobDescriptions });

  const [mode, setMode] = useState<TargetMode>("role");
  const [roleId, setRoleId] = useState("");
  const [jdId, setJdId] = useState("");

  const targetRoleId = profileQuery.data?.target_role?.id ?? "";
  const defaultRoleId = roleId || targetRoleId || rolesQuery.data?.[0]?.id || "";
  const defaultJdId = jdId || jdListQuery.data?.[0]?.id || "";

  useEffect(() => {
    if (!roleId && targetRoleId) setRoleId(targetRoleId);
  }, [roleId, targetRoleId]);

  useEffect(() => {
    if (!jdId && jdListQuery.data?.[0]?.id) setJdId(jdListQuery.data[0].id);
  }, [jdId, jdListQuery.data]);

  const queryParams =
    mode === "jd"
      ? defaultJdId
        ? { job_description_id: defaultJdId }
        : undefined
      : defaultRoleId
        ? { role_id: defaultRoleId }
        : undefined;

  const gapQuery = useQuery({
    queryKey: ["gap-analysis", mode, queryParams?.role_id, queryParams?.job_description_id],
    queryFn: () => fetchGapAnalysis(queryParams),
    enabled: Boolean(queryParams),
    retry: false,
  });

  const analysis = gapQuery.data;
  const chartGaps = (analysis?.gaps ?? []).filter((item) => item.priority !== "NONE").slice(0, 8);

  return (
    <div className="space-y-6">
      <section className="rounded-xl border border-slate-200 bg-white p-6">
        <h2 className="text-lg font-semibold text-navy-900">Compare against</h2>
        <div className="mt-4 grid gap-4 md:grid-cols-2">
          <label className="text-sm text-slate-600">
            Target
            <select
              className={`${inputClass} mt-1`}
              value={mode}
              onChange={(event) => setMode(event.target.value as TargetMode)}
            >
              <option value="role">Catalog role</option>
              <option value="jd">Saved job description</option>
            </select>
          </label>
          {mode === "role" ? (
            <label className="text-sm text-slate-600">
              Role
              <select
                className={`${inputClass} mt-1`}
                value={defaultRoleId}
                onChange={(event) => setRoleId(event.target.value)}
              >
                {(rolesQuery.data ?? []).map((item) => (
                  <option key={item.id} value={item.id}>
                    {item.title}
                    {item.id === targetRoleId ? " (your target)" : ""}
                  </option>
                ))}
              </select>
            </label>
          ) : (
            <label className="text-sm text-slate-600">
              Job description
              <select
                className={`${inputClass} mt-1`}
                value={defaultJdId}
                onChange={(event) => setJdId(event.target.value)}
              >
                {(jdListQuery.data ?? []).map((item) => (
                  <option key={item.id} value={item.id}>
                    {item.title}
                  </option>
                ))}
              </select>
            </label>
          )}
        </div>
        {mode === "jd" && !jdListQuery.data?.length ? (
          <p className="mt-3 text-sm text-slate-500">
            Analyze a job description on Roles first, then return here.
          </p>
        ) : null}
      </section>

      {gapQuery.isError ? (
        <p className="text-sm text-red-600">
          {getErrorMessage(gapQuery.error, "Select a target role or analyze a job description first.")}
        </p>
      ) : null}

      {analysis ? (
        <>
          <div className="grid gap-4 md:grid-cols-3 lg:grid-cols-6">
            <StatCard label="Target" value={analysis.target.title} />
            <StatCard label="Open gaps" value={String(analysis.gap_count)} />
            <StatCard label="Critical" value={String(analysis.critical_count)} />
            <StatCard label="High" value={String(analysis.high_count)} />
            <StatCard label="Medium" value={String(analysis.medium_count)} />
            <StatCard label="Low" value={String(analysis.low_count)} />
          </div>

          <section className="rounded-xl border border-slate-200 bg-white p-6">
            <h2 className="text-lg font-semibold text-navy-900">Priority</h2>
            {chartGaps.length ? <GapBars items={chartGaps} /> : (
              <p className="mt-4 text-sm text-slate-500">No open gaps against this target.</p>
            )}
          </section>

          <ul className="space-y-3">
            {analysis.gaps.map((item) => (
              <GapCard key={item.skill.id} item={item} />
            ))}
          </ul>
        </>
      ) : null}

      {!queryParams && !gapQuery.isFetching && !rolesQuery.isLoading ? (
        <p className="text-sm text-slate-500">
          Select a target role on your profile, or analyze a job description, then compare here.
        </p>
      ) : null}
    </div>
  );
}

function GapCard({ item }: { item: GapItem }) {
  const current = num(item.current_level);
  const required = num(item.required_level);
  return (
    <li className="rounded-xl border border-slate-200 bg-white p-5">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <p className="font-medium text-navy-900">{item.skill.canonical_name}</p>
        <div className="flex flex-wrap gap-2">
          <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${PRIORITY_STYLE[item.priority]}`}>
            {item.priority.toLowerCase()}
          </span>
          <span className="rounded-full bg-slate-100 px-2 py-0.5 text-xs font-medium text-slate-700">
            {item.requirement.toLowerCase()}
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
        Gap {num(item.gap)} · {current}/{required}
      </p>
      <LevelBars current={current} required={required} />
    </li>
  );
}

function LevelBars({ current, required }: { current: number; required: number }) {
  return (
    <div className="mt-4 space-y-2">
      <LevelBar label="Current" value={current} tone="bg-navy-700" />
      <LevelBar label="Required" value={required} tone="bg-teal-600" />
    </div>
  );
}

function LevelBar({
  label,
  value,
  tone,
}: {
  label: string;
  value: number;
  tone: string;
}) {
  const width = Math.max(0, Math.min(100, (value / 5) * 100));
  return (
    <div>
      <div className="mb-1 flex justify-between text-xs text-slate-500">
        <span>{label}</span>
        <span>{value}/5</span>
      </div>
      <div className="h-2 overflow-hidden rounded-full bg-slate-100">
        <div className={`h-full rounded-full ${tone}`} style={{ width: `${width}%` }} />
      </div>
    </div>
  );
}

function GapBars({ items }: { items: GapItem[] }) {
  const max = useMemo(() => Math.max(2, ...items.map((item) => num(item.gap))), [items]);
  return (
    <ul className="mt-4 space-y-3">
      {items.map((item) => (
        <li key={item.skill.id}>
          <div className="mb-1 flex justify-between text-sm">
            <span className="text-slate-700">{item.skill.canonical_name}</span>
            <span className="text-slate-500">{num(item.gap)}</span>
          </div>
          <div className="h-2 overflow-hidden rounded-full bg-slate-100">
            <div
              className="h-full rounded-full bg-navy-700"
              style={{ width: `${Math.max(4, (num(item.gap) / max) * 100)}%` }}
            />
          </div>
        </li>
      ))}
    </ul>
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

function num(value: number | string): number {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : 0;
}
