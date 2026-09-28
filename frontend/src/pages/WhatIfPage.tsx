import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { PageHeader } from "../components/common/PageHeader";
import { fetchProfile, fetchRoles, fetchWhatIf } from "../services/auth";
import { getErrorMessage } from "../services/api";

export function WhatIfPage() {
  const profileQuery = useQuery({ queryKey: ["profile"], queryFn: fetchProfile });
  const rolesQuery = useQuery({ queryKey: ["roles"], queryFn: fetchRoles });
  const currentId = profileQuery.data?.target_role?.id ?? "";
  const [selected, setSelected] = useState<string[]>([]);

  const roleIds = useMemo(() => {
    if (selected.length) {
      return selected;
    }
    const roles = rolesQuery.data ?? [];
    const defaults: string[] = [];
    if (currentId) {
      defaults.push(currentId);
    }
    for (const role of roles) {
      if (defaults.length >= 3) {
        break;
      }
      if (!defaults.includes(role.id)) {
        defaults.push(role.id);
      }
    }
    return defaults;
  }, [selected, rolesQuery.data, currentId]);

  const compareQuery = useQuery({
    queryKey: ["what-if", roleIds],
    queryFn: () => fetchWhatIf(roleIds),
    enabled: roleIds.length >= 1,
    retry: false,
  });

  function toggle(id: string) {
    setSelected((current) => {
      const base = current.length ? current : roleIds;
      if (base.includes(id)) {
        return base.filter((item) => item !== id);
      }
      if (base.length >= 4) {
        return base;
      }
      return [...base, id];
    });
  }

  const data = compareQuery.data;
  const error = compareQuery.error
    ? getErrorMessage(compareQuery.error, "Unable to compare roles.")
    : null;

  return (
    <div className="space-y-6">
      <PageHeader title="Compare" note="Not a hiring prediction." />

      <section className="rounded-xl border border-slate-200 bg-white p-6">
        <h2 className="text-lg font-semibold text-navy-900">Catalog roles</h2>
        <p className="mt-1 text-sm text-slate-500">Select up to four roles.</p>
        <div className="mt-4 grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
          {(rolesQuery.data ?? []).map((role) => (
            <label key={role.id} className="flex items-center gap-2 text-sm text-slate-700">
              <input
                type="checkbox"
                checked={roleIds.includes(role.id)}
                onChange={() => toggle(role.id)}
              />
              {role.title}
              {role.id === currentId ? (
                <span className="text-xs text-slate-400">(current)</span>
              ) : null}
            </label>
          ))}
        </div>
      </section>

      {error ? <p className="text-sm text-red-600">{error}</p> : null}
      {compareQuery.isFetching ? (
        <p className="text-sm text-slate-500">Comparing stored skill coverage…</p>
      ) : null}

      {data ? (
        <section className="overflow-x-auto rounded-xl border border-slate-200 bg-white p-6">
          <p className="text-sm text-slate-500">{data.hours_per_week}h / week</p>
          <table className="mt-4 min-w-full text-left text-sm">
            <thead>
              <tr className="border-b border-slate-200 text-xs uppercase tracking-wide text-slate-500">
                <th className="py-2 pr-4 font-medium">Role</th>
                <th className="py-2 pr-4 font-medium">Coverage</th>
                <th className="py-2 pr-4 font-medium">Missing</th>
                <th className="py-2 pr-4 font-medium">Effort</th>
                <th className="py-2 pr-4 font-medium">Path</th>
                <th className="py-2 pr-4 font-medium">Projects</th>
                <th className="py-2 font-medium">Mentors</th>
              </tr>
            </thead>
            <tbody>
              {data.scenarios.map((item) => (
                <tr key={item.role.id} className="border-b border-slate-100 align-top">
                  <td className="py-3 pr-4 font-medium text-navy-900">
                    {item.role.title}
                    {item.is_current ? (
                      <span className="block text-xs font-normal text-slate-400">
                        Current target
                      </span>
                    ) : null}
                  </td>
                  <td className="py-3 pr-4 text-slate-600">
                    {Math.round(item.coverage * 100)}%
                    <span className="block text-xs text-slate-400">
                      {item.covered_count}/{item.skill_count} skills
                    </span>
                  </td>
                  <td className="py-3 pr-4 text-slate-600">
                    {item.open_gap_count === 0
                      ? "None open"
                      : item.missing_skills
                          .slice(0, 4)
                          .map((gap) => gap.skill)
                          .join(", ")}
                  </td>
                  <td className="py-3 pr-4 text-slate-600">
                    {item.estimated_hours}h
                    <span className="block text-xs text-slate-400">
                      {item.estimated_weeks} week(s)
                    </span>
                  </td>
                  <td className="py-3 pr-4 text-slate-600">
                    {item.path_skills.length ? item.path_skills.join(" → ") : "—"}
                  </td>
                  <td className="py-3 pr-4 text-slate-600">
                    {item.required_projects.length
                      ? item.required_projects.join(", ")
                      : "—"}
                  </td>
                  <td className="py-3 text-slate-600">
                    {item.mentor_count
                      ? `${item.mentor_count}: ${item.mentor_names.join(", ")}`
                      : "None covering open gaps"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      ) : null}
    </div>
  );
}
