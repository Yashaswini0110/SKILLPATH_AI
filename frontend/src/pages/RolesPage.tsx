import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { type FormEvent, useMemo, useState } from "react";
import {
  analyzeJobDescription,
  fetchJobDescription,
  fetchJobDescriptions,
  fetchProfile,
  fetchRole,
  fetchRoles,
  uploadJobDescription,
} from "../services/auth";
import { getErrorMessage } from "../services/api";
import { PageHeader } from "../components/common/PageHeader";
import { inputClass } from "../components/common/AuthCard";
import type { JobDescriptionSkill, RequirementType, RoleSkill } from "../types/api";

const GROUPS: { key: RequirementType; label: string }[] = [
  { key: "REQUIRED", label: "Required" },
  { key: "PREFERRED", label: "Preferred" },
  { key: "MENTIONED", label: "Mentioned" },
];

export function RolesPage() {
  const queryClient = useQueryClient();
  const profileQuery = useQuery({ queryKey: ["profile"], queryFn: fetchProfile });
  const rolesQuery = useQuery({ queryKey: ["roles"], queryFn: fetchRoles });
  const jdListQuery = useQuery({ queryKey: ["job-descriptions"], queryFn: fetchJobDescriptions });

  const [roleId, setRoleId] = useState<string | null>(null);
  const [jdId, setJdId] = useState<string | null>(null);
  const [pasteTitle, setPasteTitle] = useState("");
  const [pasteText, setPasteText] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  const selectedRoleId =
    roleId ?? profileQuery.data?.target_role?.id ?? rolesQuery.data?.[0]?.id ?? null;
  const latestJd = jdListQuery.data?.[0];
  const activeJdId = jdId ?? latestJd?.id ?? null;

  const roleDetailQuery = useQuery({
    queryKey: ["role", selectedRoleId],
    queryFn: () => fetchRole(selectedRoleId as string),
    enabled: Boolean(selectedRoleId),
  });
  const jdDetailQuery = useQuery({
    queryKey: ["job-description", activeJdId],
    queryFn: () => fetchJobDescription(activeJdId as string),
    enabled: Boolean(activeJdId),
  });

  const analyze = useMutation({
    mutationFn: analyzeJobDescription,
    onSuccess: async (result) => {
      setJdId(result.id);
      setMessage(
        result.skills.length
          ? `Mapped ${result.skills.length} catalog skill(s) from the job description.`
          : "No catalog skills were found. Unknown terms are left unmatched.",
      );
      setError(null);
      await queryClient.invalidateQueries({ queryKey: ["job-descriptions"] });
    },
    onError: (err) => setError(getErrorMessage(err, "Unable to analyze job description")),
  });

  const upload = useMutation({
    mutationFn: ({ file, title }: { file: File; title?: string }) =>
      uploadJobDescription(file, title),
    onSuccess: async (result) => {
      setJdId(result.id);
      setMessage(
        result.skills.length
          ? `Mapped ${result.skills.length} catalog skill(s) from the uploaded file.`
          : "No catalog skills were found. Unknown terms are left unmatched.",
      );
      setError(null);
      await queryClient.invalidateQueries({ queryKey: ["job-descriptions"] });
    },
    onError: (err) => setError(getErrorMessage(err, "Unable to analyze job description")),
  });

  async function onPaste(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (pasteText.trim().length < 20) {
      setError("Paste a longer job description first.");
      return;
    }
    await analyze.mutateAsync({
      title: pasteTitle.trim() || undefined,
      text: pasteText,
    });
  }

  async function onUpload(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const file = form.get("file");
    const title = String(form.get("title") || "").trim();
    if (!(file instanceof File) || file.size === 0) {
      setError("Choose a PDF, DOCX, or TXT job description first.");
      return;
    }
    await upload.mutateAsync({ file, title: title || undefined });
  }

  const role = roleDetailQuery.data;
  const jd = jdDetailQuery.data;
  const busy = analyze.isPending || upload.isPending;

  return (
    <div className="space-y-6">
      <PageHeader title="Roles" />

      <section className="rounded-xl border border-slate-200 bg-white p-6">
        <h2 className="text-lg font-semibold text-navy-900">Catalog role</h2>
        <select
          className={`${inputClass} mt-4`}
          value={selectedRoleId ?? ""}
          onChange={(event) => setRoleId(event.target.value)}
        >
          {(rolesQuery.data ?? []).map((item) => (
            <option key={item.id} value={item.id}>
              {item.title}
            </option>
          ))}
        </select>
        {role ? (
          <div className="mt-5">
            <p className="text-sm text-slate-500">{role.description}</p>
            <SkillGroups
              items={role.skills}
              weights={role.weights}
            />
          </div>
        ) : null}
      </section>

      <section className="rounded-xl border border-slate-200 bg-white p-6">
        <h2 className="text-lg font-semibold text-navy-900">Analyze a job description</h2>
        <form className="mt-4 space-y-3" onSubmit={onPaste}>
          <input
            className={inputClass}
            placeholder="Title (optional)"
            value={pasteTitle}
            onChange={(event) => setPasteTitle(event.target.value)}
          />
          <textarea
            className={`${inputClass} min-h-40`}
            placeholder="Paste the job description"
            value={pasteText}
            onChange={(event) => setPasteText(event.target.value)}
          />
          <button
            type="submit"
            disabled={busy}
            className="rounded-lg bg-navy-800 px-4 py-2 text-sm font-medium text-white hover:bg-navy-700 disabled:opacity-60"
          >
            {analyze.isPending ? "Analyzing..." : "Analyze pasted text"}
          </button>
        </form>
        <form className="mt-5 flex flex-col gap-3 md:flex-row md:items-end" onSubmit={onUpload}>
          <input
            name="title"
            className={inputClass}
            placeholder="Upload title (optional)"
          />
          <input
            name="file"
            type="file"
            accept=".pdf,.docx,.txt,application/pdf,text/plain"
            required
            className={inputClass}
          />
          <button
            type="submit"
            disabled={busy}
            className="rounded-lg border border-slate-300 px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50 disabled:opacity-60"
          >
            {upload.isPending ? "Uploading..." : "Analyze file"}
          </button>
        </form>
        {message ? <p className="mt-3 text-sm text-teal-800">{message}</p> : null}
        {error ? <p className="mt-3 text-sm text-red-600">{error}</p> : null}
      </section>

      <section className="rounded-xl border border-slate-200 bg-white p-6">
        <h2 className="text-lg font-semibold text-navy-900">Saved analyses</h2>
        <ul className="mt-3 space-y-2">
          {(jdListQuery.data ?? []).map((item) => (
            <li key={item.id}>
              <button
                type="button"
                className="w-full rounded-lg bg-slate-50 p-3 text-left hover:bg-slate-100"
                onClick={() => setJdId(item.id)}
              >
                <p className="font-medium text-slate-800">{item.title}</p>
                <p className="text-sm text-slate-500">
                  {item.source_type === "FILE" ? "Uploaded file" : "Pasted text"} · {item.skill_count} skills
                </p>
              </button>
            </li>
          ))}
        </ul>
        {!jdListQuery.data?.length ? (
          <p className="mt-2 text-sm text-slate-500">No job descriptions analyzed yet.</p>
        ) : null}
      </section>

      {activeJdId && jd ? (
        <section className="rounded-xl border border-slate-200 bg-white p-6">
          <h2 className="text-lg font-semibold text-navy-900">{jd.title}</h2>
          <p className="mt-1 text-sm text-slate-500">Job skill profile</p>
          <SkillGroups items={jd.skills} weights={jd.weights} />
        </section>
      ) : null}
    </div>
  );
}

function formatWeight(value: string): string {
  const numeric = Number(value);
  if (Number.isNaN(numeric)) return value;
  return numeric.toFixed(1);
}

function SkillGroups({
  items,
  weights,
}: {
  items: Array<RoleSkill | JobDescriptionSkill>;
  weights: { required: number; preferred: number; mentioned: number };
}) {
  const grouped = useMemo(() => {
    const buckets: Record<RequirementType, Array<RoleSkill | JobDescriptionSkill>> = {
      REQUIRED: [],
      PREFERRED: [],
      MENTIONED: [],
    };
    for (const item of items) {
      buckets[item.requirement].push(item);
    }
    return buckets;
  }, [items]);

  const weightLabel: Record<RequirementType, string> = {
    REQUIRED: String(weights.required),
    PREFERRED: String(weights.preferred),
    MENTIONED: String(weights.mentioned),
  };

  return (
    <div className="mt-4 grid gap-4 md:grid-cols-3">
      {GROUPS.map((group) => (
        <div key={group.key} className="rounded-lg border border-slate-200 p-4">
          <p className="text-sm font-semibold text-navy-900">{group.label}</p>
          <p className="text-xs text-slate-500">Weight {formatWeight(weightLabel[group.key])}</p>
          <ul className="mt-3 space-y-2">
            {grouped[group.key].map((item) => (
              <li key={item.skill.id} className="text-sm text-slate-700">
                <span className="font-medium">{item.skill.canonical_name}</span>
                <span className="text-slate-500"> · level {item.required_level}/5</span>
              </li>
            ))}
          </ul>
          {!grouped[group.key].length ? (
            <p className="mt-3 text-sm text-slate-400">None</p>
          ) : null}
        </div>
      ))}
    </div>
  );
}
