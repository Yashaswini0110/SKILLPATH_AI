import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { type FormEvent, useState } from "react";
import {
  addEducation,
  addExperience,
  addSkill,
  deleteEducation,
  deleteExperience,
  deleteSkill,
  fetchProfile,
  fetchRoles,
  fetchSkills,
  resolveSkills,
  updateProfile,
} from "../../services/auth";
import { getErrorMessage } from "../../services/api";
import { Field, inputClass } from "../common/AuthCard";

const FORMATS = ["video", "text", "hands-on", "live"];

export function ProfileForm() {
  const queryClient = useQueryClient();
  const profileQuery = useQuery({ queryKey: ["profile"], queryFn: fetchProfile });
  const skillsQuery = useQuery({ queryKey: ["skills"], queryFn: fetchSkills });
  const rolesQuery = useQuery({ queryKey: ["roles"], queryFn: fetchRoles });
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const saveProfile = useMutation({
    mutationFn: updateProfile,
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["profile"] });
      setMessage("Profile saved.");
      setError(null);
    },
    onError: (err) => setError(getErrorMessage(err)),
  });

  if (profileQuery.isLoading) {
    return <p className="text-sm text-slate-500">Loading profile...</p>;
  }
  if (!profileQuery.data) {
    return <p className="text-sm text-red-600">Unable to load profile.</p>;
  }

  const profile = profileQuery.data;
  const usedSkillIds = new Set(profile.skills.map((item) => item.skill.id));

  async function onSave(form: FormData) {
    const formats = FORMATS.filter((format) => form.getAll("formats").includes(format));
    await saveProfile.mutateAsync({
      job_title: String(form.get("job_title") || "") || null,
      department: String(form.get("department") || "") || null,
      years_experience: form.get("years_experience")
        ? Number(form.get("years_experience"))
        : null,
      available_hours_per_week: Number(form.get("available_hours_per_week") || 10),
      target_role_id: String(form.get("target_role_id") || "") || null,
      learning_preferences: {
        formats,
        pace: String(form.get("pace") || "") || null,
      },
    });
  }

  return (
    <div className="space-y-8">
      {message ? <p className="text-sm text-teal-700">{message}</p> : null}
      {error ? <p className="text-sm text-red-600">{error}</p> : null}

      <section className="rounded-xl border border-slate-200 bg-white p-6">
        <h2 className="text-lg font-semibold text-navy-900">Employee profile</h2>
        <p className="mt-1 text-sm text-slate-500">
          Completeness {Math.round(profile.completeness.score * 100)}% —{" "}
          {profile.completeness.completed_items}/{profile.completeness.total_items} sections
        </p>
        <form
          className="mt-4 grid gap-4 md:grid-cols-2"
          onSubmit={(event) => {
            event.preventDefault();
            void onSave(new FormData(event.currentTarget));
          }}
        >
          <Field label="Full name">
            <input className={inputClass} value={profile.full_name} disabled />
          </Field>
          <Field label="Email">
            <input className={inputClass} value={profile.email} disabled />
          </Field>
          <Field label="Job title">
            <input
              name="job_title"
              className={inputClass}
              defaultValue={profile.job_title ?? ""}
              placeholder="Software Engineer"
            />
          </Field>
          <Field label="Department">
            <input
              name="department"
              className={inputClass}
              defaultValue={profile.department ?? ""}
              placeholder="Engineering"
            />
          </Field>
          <Field label="Years of experience">
            <input
              name="years_experience"
              type="number"
              min={0}
              step="0.1"
              className={inputClass}
              defaultValue={profile.years_experience ?? ""}
            />
          </Field>
          <Field label="Available hours per week">
            <input
              name="available_hours_per_week"
              type="number"
              min={1}
              max={80}
              className={inputClass}
              defaultValue={profile.available_hours_per_week}
            />
          </Field>
          <Field label="Target role">
            <select
              name="target_role_id"
              className={inputClass}
              defaultValue={profile.target_role?.id ?? ""}
            >
              <option value="">Select a role</option>
              {(rolesQuery.data ?? []).map((role) => (
                <option key={role.id} value={role.id}>
                  {role.title}
                </option>
              ))}
            </select>
          </Field>
          <Field label="Learning pace">
            <input
              name="pace"
              className={inputClass}
              defaultValue={profile.learning_preferences?.pace ?? ""}
              placeholder="moderate"
            />
          </Field>
          <div className="md:col-span-2">
            <p className="mb-2 text-sm font-medium text-slate-700">Learning formats</p>
            <div className="flex flex-wrap gap-3">
              {FORMATS.map((format) => (
                <label key={format} className="flex items-center gap-2 text-sm text-slate-700">
                  <input
                    type="checkbox"
                    name="formats"
                    value={format}
                    defaultChecked={profile.learning_preferences?.formats.includes(format)}
                  />
                  {format}
                </label>
              ))}
            </div>
          </div>
          <div className="md:col-span-2">
            <button
              type="submit"
              className="rounded-lg bg-navy-800 px-4 py-2 text-sm font-medium text-white hover:bg-navy-700"
            >
              Save profile
            </button>
          </div>
        </form>
      </section>

      <EducationSection
        items={profile.education}
        onAdded={() => void queryClient.invalidateQueries({ queryKey: ["profile"] })}
      />
      <ExperienceSection
        items={profile.experience}
        onAdded={() => void queryClient.invalidateQueries({ queryKey: ["profile"] })}
      />
      <SkillsSection
        items={profile.skills}
        catalog={(skillsQuery.data ?? []).filter((skill) => !usedSkillIds.has(skill.id))}
        onAdded={() => {
          void queryClient.invalidateQueries({ queryKey: ["profile"] });
          void queryClient.invalidateQueries({ queryKey: ["skill-profile"] });
        }}
      />
    </div>
  );
}

function EducationSection({
  items,
  onAdded,
}: {
  items: EmployeeProfileEducation[];
  onAdded: () => void;
}) {
  return (
    <section className="rounded-xl border border-slate-200 bg-white p-6">
      <h2 className="text-lg font-semibold text-navy-900">Education</h2>
      <ul className="mt-3 space-y-2">
        {items.map((item) => (
          <li key={item.id} className="flex items-start justify-between rounded-lg bg-slate-50 p-3">
            <div>
              <p className="font-medium text-slate-800">{item.degree}</p>
              <p className="text-sm text-slate-500">
                {item.institution}
                {item.field_of_study ? ` · ${item.field_of_study}` : ""}
              </p>
            </div>
            <button
              className="text-sm text-red-600"
              type="button"
              onClick={async () => {
                await deleteEducation(item.id);
                onAdded();
              }}
            >
              Remove
            </button>
          </li>
        ))}
      </ul>
      <form
        className="mt-4 grid gap-3 md:grid-cols-2"
        onSubmit={async (event) => {
          event.preventDefault();
          const formEl = event.currentTarget;
          const form = new FormData(formEl);
          await addEducation({
            degree: String(form.get("degree")),
            institution: String(form.get("institution")),
            field_of_study: String(form.get("field_of_study") || "") || null,
            start_year: form.get("start_year") ? Number(form.get("start_year")) : null,
            end_year: form.get("end_year") ? Number(form.get("end_year")) : null,
          });
          formEl.reset();
          onAdded();
        }}
      >
        <input name="degree" required placeholder="Degree" className={inputClass} />
        <input name="institution" required placeholder="Institution" className={inputClass} />
        <input name="field_of_study" placeholder="Field of study" className={inputClass} />
        <div className="grid grid-cols-2 gap-3">
          <input name="start_year" type="number" placeholder="Start year" className={inputClass} />
          <input name="end_year" type="number" placeholder="End year" className={inputClass} />
        </div>
        <button className="rounded-lg border border-slate-300 px-4 py-2 text-sm" type="submit">
          Add education
        </button>
      </form>
    </section>
  );
}

function ExperienceSection({
  items,
  onAdded,
}: {
  items: EmployeeProfileExperience[];
  onAdded: () => void;
}) {
  return (
    <section className="rounded-xl border border-slate-200 bg-white p-6">
      <h2 className="text-lg font-semibold text-navy-900">Work experience</h2>
      <ul className="mt-3 space-y-2">
        {items.map((item) => (
          <li key={item.id} className="flex items-start justify-between rounded-lg bg-slate-50 p-3">
            <div>
              <p className="font-medium text-slate-800">
                {item.role_title} · {item.company}
              </p>
              <p className="text-sm text-slate-500">
                {item.start_date} – {item.is_current ? "present" : item.end_date}
              </p>
            </div>
            <button
              className="text-sm text-red-600"
              type="button"
              onClick={async () => {
                await deleteExperience(item.id);
                onAdded();
              }}
            >
              Remove
            </button>
          </li>
        ))}
      </ul>
      <form
        className="mt-4 grid gap-3 md:grid-cols-2"
        onSubmit={async (event) => {
          event.preventDefault();
          const formEl = event.currentTarget;
          const form = new FormData(formEl);
          const isCurrent = form.get("is_current") === "on";
          await addExperience({
            company: String(form.get("company")),
            role_title: String(form.get("role_title")),
            description: String(form.get("description") || "") || null,
            start_date: String(form.get("start_date")),
            end_date: isCurrent ? null : String(form.get("end_date") || "") || null,
            is_current: isCurrent,
          });
          formEl.reset();
          onAdded();
        }}
      >
        <input name="company" required placeholder="Company" className={inputClass} />
        <input name="role_title" required placeholder="Role" className={inputClass} />
        <input name="start_date" required type="date" className={inputClass} />
        <input name="end_date" type="date" className={inputClass} />
        <label className="flex items-center gap-2 text-sm text-slate-700">
          <input type="checkbox" name="is_current" />
          Current role
        </label>
        <textarea name="description" placeholder="Description" className={inputClass} />
        <button className="rounded-lg border border-slate-300 px-4 py-2 text-sm" type="submit">
          Add experience
        </button>
      </form>
    </section>
  );
}

function SkillsSection({
  items,
  catalog,
  onAdded,
}: {
  items: import("../../types/api").EmployeeSkill[];
  catalog: import("../../types/api").Skill[];
  onAdded: () => void;
}) {
  return (
    <section className="rounded-xl border border-slate-200 bg-white p-6">
      <h2 className="text-lg font-semibold text-navy-900">Self-declared skills</h2>
      <p className="mt-1 text-sm text-slate-500">
        These values are self-reported, not verified evidence. Mentions such as ML or K8s
        map to one canonical skill. Unknown terms are left unmatched.
      </p>
      <TaxonomyLookup />
      <ul className="mt-3 space-y-2">
        {items.map((item) => (
          <li key={item.id} className="flex items-center justify-between rounded-lg bg-slate-50 p-3">
            <div>
              <p className="font-medium text-slate-800">{item.skill.canonical_name}</p>
              <p className="text-sm text-slate-500">
                Level {item.current_level}/5 · {item.source_type} · confidence {item.confidence}
                {item.skill.aliases.length ? ` · aliases ${item.skill.aliases.slice(0, 3).join(", ")}` : ""}
              </p>
            </div>
            <button
              className="text-sm text-red-600"
              type="button"
              onClick={async () => {
                await deleteSkill(item.id);
                onAdded();
              }}
            >
              Remove
            </button>
          </li>
        ))}
      </ul>
      <form
        className="mt-4 grid gap-3 md:grid-cols-3"
        onSubmit={async (event) => {
          event.preventDefault();
          const formEl = event.currentTarget;
          const form = new FormData(formEl);
          await addSkill({
            skill_id: String(form.get("skill_id")),
            current_level: Number(form.get("current_level")),
          });
          formEl.reset();
          onAdded();
        }}
      >
        <select name="skill_id" required className={inputClass}>
          <option value="">Select skill</option>
          {catalog.map((skill) => (
            <option key={skill.id} value={skill.id}>
              {skill.canonical_name}
              {skill.aliases.length ? ` (${skill.aliases.slice(0, 2).join(", ")})` : ""}
            </option>
          ))}
        </select>
        <input
          name="current_level"
          type="number"
          min={1}
          max={5}
          step="0.5"
          defaultValue={3}
          className={inputClass}
        />
        <button className="rounded-lg border border-slate-300 px-4 py-2 text-sm" type="submit">
          Add skill
        </button>
      </form>
    </section>
  );
}

function TaxonomyLookup() {
  const [mention, setMention] = useState("");
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);

  async function onResolve(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setPending(true);
    setError(null);
    setMessage(null);
    try {
      const payload = await resolveSkills([mention]);
      const result = payload.results[0];
      if (!result || result.match_type === "unmatched" || result.match_type === "collision") {
        setMessage(
          result?.match_type === "collision"
            ? `"${mention}" matches more than one skill and was left unmatched.`
            : `"${mention}" is not in the taxonomy. The system will not invent a skill.`,
        );
      } else {
        setMessage(
          `${result.raw} → ${result.canonical_name} (${result.match_type}, confidence ${result.confidence})`,
        );
      }
    } catch (err) {
      setError(getErrorMessage(err, "Unable to resolve mention"));
    } finally {
      setPending(false);
    }
  }

  return (
    <form className="mt-4 rounded-lg border border-slate-200 bg-slate-50 p-3" onSubmit={onResolve}>
      <p className="text-sm font-medium text-slate-700">Lookup a mention</p>
      <div className="mt-2 flex gap-2">
        <input
          className={inputClass}
          value={mention}
          onChange={(event) => setMention(event.target.value)}
          placeholder="Try ML, K8s, or Postgres"
          required
        />
        <button className="rounded-lg border border-slate-300 px-3 py-2 text-sm" type="submit" disabled={pending}>
          {pending ? "..." : "Resolve"}
        </button>
      </div>
      {message ? <p className="mt-2 text-sm text-teal-800">{message}</p> : null}
      {error ? <p className="mt-2 text-sm text-red-600">{error}</p> : null}
    </form>
  );
}

type EmployeeProfileEducation = import("../../types/api").Education;
type EmployeeProfileExperience = import("../../types/api").Experience;
