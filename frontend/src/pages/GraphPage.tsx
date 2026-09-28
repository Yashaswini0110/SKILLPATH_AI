import { useEffect, useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { fetchGraphSkill, fetchGraphStatus, fetchSkills } from "../services/auth";
import { getErrorMessage } from "../services/api";
import { inputClass } from "../components/common/AuthCard";
import type { Course, GraphEdge, Mentor, Project, Skill } from "../types/api";

const NODE_W = 148;
const NODE_H = 42;
const COL_W = 164;
const ROW_H = 96;

export function GraphPanel() {
  const [skillId, setSkillId] = useState("");
  const skillsQuery = useQuery({ queryKey: ["skills"], queryFn: () => fetchSkills() });
  const statusQuery = useQuery({
    queryKey: ["graph-status"],
    queryFn: fetchGraphStatus,
    retry: false,
  });
  const viewQuery = useQuery({
    queryKey: ["graph-skill", skillId],
    queryFn: () => fetchGraphSkill(skillId),
    enabled: Boolean(skillId),
    retry: false,
  });

  useEffect(() => {
    if (skillId || !skillsQuery.data?.length) return;
    const rag = skillsQuery.data.find((item) => item.name === "RAG");
    setSkillId(rag?.id ?? skillsQuery.data[0].id);
  }, [skillId, skillsQuery.data]);

  const status = statusQuery.data;
  const view = viewQuery.data;

  return (
    <div className="space-y-6">
      <section className="rounded-xl border border-slate-200 bg-white p-6">
        <div className="flex flex-wrap items-end gap-4">
          <label className="min-w-[16rem] flex-1 text-sm text-slate-600">
            Skill
            <select
              className={`${inputClass} mt-1`}
              value={skillId}
              onChange={(event) => setSkillId(event.target.value)}
            >
              {(skillsQuery.data ?? []).map((skill) => (
                <option key={skill.id} value={skill.id}>
                  {skill.canonical_name}
                </option>
              ))}
            </select>
          </label>
          {status ? (
            <p className="text-sm text-slate-600">
              {status.acyclic ? "Prerequisite graph is acyclic" : "Cycle detected"}
              {` · ${status.nodes.Skill ?? 0} skills`}
            </p>
          ) : null}
        </div>
        {statusQuery.isError ? (
          <p className="mt-3 text-sm text-red-600">
            {getErrorMessage(statusQuery.error, "Neo4j is not reachable.")}
          </p>
        ) : null}
      </section>

      {viewQuery.isPending && skillId ? (
        <p className="text-sm text-slate-500">Loading graph…</p>
      ) : null}
      {viewQuery.isError ? (
        <p className="text-sm text-red-600">
          {getErrorMessage(viewQuery.error, "Unable to load this skill from the graph.")}
        </p>
      ) : null}

      {view ? (
        <>
          <DagCard
            layers={view.layers}
            edges={view.edges}
            currentId={view.skill.id}
            onSelect={setSkillId}
          />
          <section className="grid gap-4 lg:grid-cols-2">
            <SkillList
              title="Immediate prerequisites"
              items={view.prerequisites}
              empty="None — this skill has no graph parents."
            />
            <SkillList
              title="Related / complementary"
              items={view.related.map((row) => row.skill)}
              empty="None"
            />
          </section>
          <ResourceBlock
            courses={view.courses}
            projects={view.projects}
            mentors={view.mentors}
          />
        </>
      ) : null}
    </div>
  );
}

function DagCard({
  layers,
  edges,
  currentId,
  onSelect,
}: {
  layers: Skill[][];
  edges: GraphEdge[];
  currentId: string;
  onSelect: (id: string) => void;
}) {
  const layout = useMemo(() => layoutDag(layers), [layers]);
  if (!layers.length) return null;
  return (
    <section className="rounded-xl border border-slate-200 bg-white p-6">
      <h2 className="font-semibold text-navy-900">Prerequisites</h2>
      <div className="mt-4 overflow-x-auto">
        <svg
          width={layout.width}
          height={layout.height}
          viewBox={`0 0 ${layout.width} ${layout.height}`}
          className="max-w-none"
        >
          {edges.map((edge) => {
            const from = layout.positions.get(edge.source.id);
            const to = layout.positions.get(edge.target.id);
            if (!from || !to) return null;
            const x1 = from.x + NODE_W / 2;
            const y1 = from.y + NODE_H;
            const x2 = to.x + NODE_W / 2;
            const y2 = to.y;
            return (
              <path
                key={`${edge.source.id}-${edge.target.id}`}
                d={`M ${x1} ${y1} C ${x1} ${y1 + 28}, ${x2} ${y2 - 28}, ${x2} ${y2}`}
                fill="none"
                stroke="#94a3b8"
                strokeWidth="1.5"
                markerEnd="url(#arrow)"
              />
            );
          })}
          <defs>
            <marker
              id="arrow"
              viewBox="0 0 10 10"
              refX="8"
              refY="5"
              markerWidth="7"
              markerHeight="7"
              orient="auto-start-reverse"
            >
              <path d="M 0 0 L 10 5 L 0 10 z" fill="#94a3b8" />
            </marker>
          </defs>
          {layers.flat().map((skill) => {
            const pos = layout.positions.get(skill.id);
            if (!pos) return null;
            const active = skill.id === currentId;
            return (
              <g
                key={skill.id}
                transform={`translate(${pos.x}, ${pos.y})`}
                className="cursor-pointer"
                onClick={() => onSelect(skill.id)}
              >
                <title>{skill.canonical_name}</title>
                <rect
                  width={NODE_W}
                  height={NODE_H}
                  rx="10"
                  fill={active ? "#1e3a5f" : "#f8fafc"}
                  stroke={active ? "#1e3a5f" : "#e2e8f0"}
                />
                <text
                  x={NODE_W / 2}
                  y={NODE_H / 2 + 4}
                  textAnchor="middle"
                  fontSize="12"
                  fill={active ? "#ffffff" : "#334155"}
                >
                  {shortLabel(skill)}
                </text>
              </g>
            );
          })}
        </svg>
      </div>
    </section>
  );
}

function layoutDag(layers: Skill[][]) {
  const width = Math.max(...layers.map((layer) => layer.length), 1) * COL_W + 24;
  const height = layers.length * ROW_H + 8;
  const positions = new Map<string, { x: number; y: number }>();
  layers.forEach((layer, row) => {
    const start = (width - layer.length * COL_W) / 2;
    layer.forEach((skill, col) => {
      positions.set(skill.id, { x: start + col * COL_W + 8, y: row * ROW_H + 8 });
    });
  });
  return { width, height, positions };
}

function shortLabel(skill: Skill): string {
  const label = skill.name || skill.canonical_name;
  return label.length > 22 ? `${label.slice(0, 20)}…` : label;
}

function SkillList({
  title,
  items,
  empty,
}: {
  title: string;
  items: Skill[];
  empty: string;
}) {
  return (
    <section className="rounded-xl border border-slate-200 bg-white p-6">
      <h2 className="font-semibold text-navy-900">{title}</h2>
      {items.length ? (
        <ul className="mt-3 flex flex-wrap gap-2">
          {items.map((skill) => (
            <li
              key={skill.id}
              className="rounded-lg bg-slate-50 px-3 py-1.5 text-sm text-slate-700"
            >
              {skill.canonical_name}
            </li>
          ))}
        </ul>
      ) : (
        <p className="mt-3 text-sm text-slate-500">{empty}</p>
      )}
    </section>
  );
}

function ResourceBlock({
  courses,
  projects,
  mentors,
}: {
  courses: Course[];
  projects: Project[];
  mentors: Mentor[];
}) {
  return (
    <section className="grid gap-4 lg:grid-cols-3">
      <SimpleList
        title="Courses that teach it"
        items={courses.map((item) => item.title)}
      />
      <SimpleList
        title="Projects that practice it"
        items={projects.map((item) => item.title)}
      />
      <SimpleList title="Mentors" items={mentors.map((item) => item.name)} />
    </section>
  );
}

function SimpleList({ title, items }: { title: string; items: string[] }) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-6">
      <h2 className="font-semibold text-navy-900">{title}</h2>
      {items.length ? (
        <ul className="mt-3 list-disc space-y-1 pl-5 text-sm text-slate-600">
          {items.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      ) : (
        <p className="mt-3 text-sm text-slate-500">None in the catalog.</p>
      )}
    </div>
  );
}
