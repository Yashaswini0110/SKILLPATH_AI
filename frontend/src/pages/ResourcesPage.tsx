import { useQuery } from "@tanstack/react-query";
import { type ReactNode, useState } from "react";
import {
  fetchCourses,
  fetchMentors,
  fetchProjects,
  fetchSkills,
} from "../services/auth";
import { PageHeader } from "../components/common/PageHeader";
import { inputClass } from "../components/common/AuthCard";
import type { Course, Mentor, Project, ResourceSkill } from "../types/api";

type Tab = "courses" | "projects" | "mentors";

export function ResourcesPage() {
  const [tab, setTab] = useState<Tab>("courses");
  const [skillId, setSkillId] = useState("");
  const skillsQuery = useQuery({ queryKey: ["skills"], queryFn: () => fetchSkills() });
  const filter = skillId || undefined;

  const coursesQuery = useQuery({
    queryKey: ["courses", filter],
    queryFn: () => fetchCourses(filter),
  });
  const projectsQuery = useQuery({
    queryKey: ["projects", filter],
    queryFn: () => fetchProjects(filter),
  });
  const mentorsQuery = useQuery({
    queryKey: ["mentors", filter],
    queryFn: () => fetchMentors(filter),
  });

  return (
    <div className="space-y-6">
      <PageHeader title="Catalog" />

      <section className="rounded-xl border border-slate-200 bg-white p-6">
        <label className="text-sm text-slate-600">
          Filter by skill
          <select
            className={`${inputClass} mt-1`}
            value={skillId}
            onChange={(event) => setSkillId(event.target.value)}
          >
            <option value="">All catalog skills</option>
            {(skillsQuery.data ?? []).map((skill) => (
              <option key={skill.id} value={skill.id}>
                {skill.canonical_name}
              </option>
            ))}
          </select>
        </label>
        <div className="mt-4 flex flex-wrap gap-2">
          <TabButton current={tab} id="courses" onSelect={setTab} label="Courses" />
          <TabButton current={tab} id="projects" onSelect={setTab} label="Projects" />
          <TabButton current={tab} id="mentors" onSelect={setTab} label="Mentors" />
        </div>
      </section>

      {tab === "courses" ? (
        <ResourceList
          isPending={coursesQuery.isPending}
          isError={coursesQuery.isError}
          empty="No courses in the catalog yet."
        >
          {(coursesQuery.data ?? []).map((item) => (
            <CourseCard key={item.id} item={item} />
          ))}
        </ResourceList>
      ) : null}
      {tab === "projects" ? (
        <ResourceList
          isPending={projectsQuery.isPending}
          isError={projectsQuery.isError}
          empty="No projects in the catalog yet."
        >
          {(projectsQuery.data ?? []).map((item) => (
            <ProjectCard key={item.id} item={item} />
          ))}
        </ResourceList>
      ) : null}
      {tab === "mentors" ? (
        <ResourceList
          isPending={mentorsQuery.isPending}
          isError={mentorsQuery.isError}
          empty="No mentors in the catalog yet."
        >
          {(mentorsQuery.data ?? []).map((item) => (
            <MentorCard key={item.id} item={item} />
          ))}
        </ResourceList>
      ) : null}
    </div>
  );
}

function TabButton({
  current,
  id,
  label,
  onSelect,
}: {
  current: Tab;
  id: Tab;
  label: string;
  onSelect: (tab: Tab) => void;
}) {
  const active = current === id;
  return (
    <button
      type="button"
      onClick={() => onSelect(id)}
      className={[
        "rounded-lg px-3 py-1.5 text-sm font-medium",
        active ? "bg-navy-800 text-white" : "border border-slate-300 text-slate-700",
      ].join(" ")}
    >
      {label}
    </button>
  );
}

function CourseCard({ item }: { item: Course }) {
  return (
    <li className="rounded-xl border border-slate-200 bg-white p-5">
      <p className="font-medium text-navy-900">{item.title}</p>
      <p className="mt-1 text-sm text-slate-500">
        {item.duration_hours}h · {item.difficulty}/5
      </p>
      <SkillChips items={item.skills} />
    </li>
  );
}

function ProjectCard({ item }: { item: Project }) {
  return (
    <li className="rounded-xl border border-slate-200 bg-white p-5">
      <p className="font-medium text-navy-900">{item.title}</p>
      <p className="mt-1 text-sm text-slate-500">
        {item.duration_hours}h · {item.difficulty}/5
      </p>
      <SkillChips items={item.skills} />
    </li>
  );
}

function MentorCard({ item }: { item: Mentor }) {
  return (
    <li className="rounded-xl border border-slate-200 bg-white p-5">
      <p className="font-medium text-navy-900">{item.name}</p>
      <p className="mt-1 text-sm text-slate-500">{item.title}</p>
      <SkillChips items={item.skills} />
    </li>
  );
}

function ResourceList({
  isPending,
  isError,
  empty,
  children,
}: {
  isPending: boolean;
  isError: boolean;
  empty: string;
  children: ReactNode;
}) {
  if (isPending) {
    return <p className="text-sm text-slate-500">Loading catalog…</p>;
  }
  if (isError) {
    return (
      <p className="text-sm text-red-600">
        Could not load the catalog. Confirm the API is running on port 8000, then refresh.
      </p>
    );
  }
  if (!Array.isArray(children) || children.length === 0) {
    return <p className="text-sm text-slate-500">{empty}</p>;
  }
  return <ul className="space-y-3">{children}</ul>;
}

function SkillChips({ items }: { items: ResourceSkill[] }) {
  return (
    <ul className="mt-3 flex flex-wrap gap-2">
      {items.map((row) => (
        <li
          key={row.skill.id}
          className="rounded-lg bg-slate-50 px-3 py-1.5 text-xs text-slate-600"
        >
          {row.skill.canonical_name} · L{row.level}
        </li>
      ))}
    </ul>
  );
}
