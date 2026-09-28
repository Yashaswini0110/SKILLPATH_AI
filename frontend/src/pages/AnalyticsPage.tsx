import { useQuery } from "@tanstack/react-query";
import { PageHeader } from "../components/common/PageHeader";
import { fetchAnalytics } from "../services/auth";
import { getErrorMessage } from "../services/api";
import { useAuthStore } from "../store/authStore";

const HR_ROLES = new Set(["HR_ADMIN", "SYSTEM_ADMIN"]);

export function AnalyticsPage() {
  const role = useAuthStore((state) => state.user?.role);
  const isHr = HR_ROLES.has(role ?? "");
  const query = useQuery({
    queryKey: ["analytics"],
    queryFn: () => fetchAnalytics(),
    retry: false,
  });
  const data = query.data;
  const error = query.error
    ? getErrorMessage(query.error, "Unable to load analytics.")
    : null;

  return (
    <div className="space-y-6">
      <PageHeader
        title={isHr ? "Organization" : "Team"}
        note="Counts only. No names."
      />

      {error ? <p className="text-sm text-red-600">{error}</p> : null}
      {query.isFetching ? (
        <p className="text-sm text-slate-500">Loading stored aggregates…</p>
      ) : null}

      {data ? (
        <>
          <p className="text-sm text-slate-600">
            {data.scope.label} · {data.employee_count} people
          </p>

          <section className="overflow-x-auto rounded-xl border border-slate-200 bg-white p-6">
            <h2 className="text-lg font-semibold text-navy-900">Heatmap</h2>
            <table className="mt-4 min-w-full text-left text-sm">
              <thead>
                <tr className="border-b border-slate-200 text-xs uppercase tracking-wide text-slate-500">
                  <th className="py-2 pr-4 font-medium">Skill</th>
                  <th className="py-2 pr-4 font-medium">1</th>
                  <th className="py-2 pr-4 font-medium">2</th>
                  <th className="py-2 pr-4 font-medium">3</th>
                  <th className="py-2 pr-4 font-medium">4</th>
                  <th className="py-2 pr-4 font-medium">5</th>
                  <th className="py-2 font-medium">Missing</th>
                </tr>
              </thead>
              <tbody>
                {data.heatmap.map((row) => (
                  <tr key={row.skill.id} className="border-b border-slate-100">
                    <td className="py-2 pr-4 font-medium text-navy-900">
                      {row.skill.canonical_name}
                    </td>
                    <td className="py-2 pr-4 text-slate-600">{row.band_1}</td>
                    <td className="py-2 pr-4 text-slate-600">{row.band_2}</td>
                    <td className="py-2 pr-4 text-slate-600">{row.band_3}</td>
                    <td className="py-2 pr-4 text-slate-600">{row.band_4}</td>
                    <td className="py-2 pr-4 text-slate-600">{row.band_5}</td>
                    <td className="py-2 text-slate-600">{row.missing_count}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            {data.heatmap.length === 0 ? (
              <p className="mt-4 text-sm text-slate-500">No skill coverage yet.</p>
            ) : null}
          </section>

          <section className="overflow-x-auto rounded-xl border border-slate-200 bg-white p-6">
            <h2 className="text-lg font-semibold text-navy-900">Top skill gaps</h2>
            <table className="mt-4 min-w-full text-left text-sm">
              <thead>
                <tr className="border-b border-slate-200 text-xs uppercase tracking-wide text-slate-500">
                  <th className="py-2 pr-4 font-medium">Skill</th>
                  <th className="py-2 pr-4 font-medium">People with a gap</th>
                  <th className="py-2 pr-4 font-medium">Average gap</th>
                  <th className="py-2 font-medium">Critical / high</th>
                </tr>
              </thead>
              <tbody>
                {data.top_gaps.map((row) => (
                  <tr key={row.skill.id} className="border-b border-slate-100">
                    <td className="py-2 pr-4 font-medium text-navy-900">
                      {row.skill.canonical_name}
                    </td>
                    <td className="py-2 pr-4 text-slate-600">{row.employees_with_gap}</td>
                    <td className="py-2 pr-4 text-slate-600">{row.avg_gap.toFixed(1)}</td>
                    <td className="py-2 text-slate-600">
                      {row.critical_count} / {row.high_count}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            {data.top_gaps.length === 0 ? (
              <p className="mt-4 text-sm text-slate-500">
                No open target-role gaps in this scope.
              </p>
            ) : null}
          </section>

          <section className="overflow-x-auto rounded-xl border border-slate-200 bg-white p-6">
            <h2 className="text-lg font-semibold text-navy-900">Training priorities</h2>
            <table className="mt-4 min-w-full text-left text-sm">
              <thead>
                <tr className="border-b border-slate-200 text-xs uppercase tracking-wide text-slate-500">
                  <th className="py-2 pr-4 font-medium">Rank</th>
                  <th className="py-2 pr-4 font-medium">Skill</th>
                  <th className="py-2 pr-4 font-medium">People</th>
                  <th className="py-2 font-medium">Catalog courses / projects</th>
                </tr>
              </thead>
              <tbody>
                {data.training_priorities.map((row) => (
                  <tr key={row.skill.id} className="border-b border-slate-100">
                    <td className="py-2 pr-4 text-slate-600">{row.rank}</td>
                    <td className="py-2 pr-4 font-medium text-navy-900">
                      {row.skill.canonical_name}
                    </td>
                    <td className="py-2 pr-4 text-slate-600">{row.employees_with_gap}</td>
                    <td className="py-2 text-slate-600">
                      {row.course_count} / {row.project_count}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </section>

          <section className="rounded-xl border border-slate-200 bg-white p-6">
            <h2 className="text-lg font-semibold text-navy-900">Learning progress</h2>
            <p className="mt-2 text-sm text-slate-600">
              {data.learning_progress.employees_with_attempts} quizzes ·{" "}
              {Math.round(data.learning_progress.pass_rate * 100)}% pass ·{" "}
              {data.learning_progress.employees_with_paths} paths
            </p>
          </section>

          <section className="overflow-x-auto rounded-xl border border-slate-200 bg-white p-6">
            <h2 className="text-lg font-semibold text-navy-900">
              Role competency frameworks
            </h2>
            <table className="mt-4 min-w-full text-left text-sm">
              <thead>
                <tr className="border-b border-slate-200 text-xs uppercase tracking-wide text-slate-500">
                  <th className="py-2 pr-4 font-medium">Catalog role</th>
                  <th className="py-2 font-medium">People targeting it</th>
                </tr>
              </thead>
              <tbody>
                {data.frameworks.map((row) => (
                  <tr key={row.role_id} className="border-b border-slate-100">
                    <td className="py-2 pr-4 font-medium text-navy-900">{row.title}</td>
                    <td className="py-2 text-slate-600">{row.employees_targeting}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </section>

          {isHr && data.departments.length ? (
            <section className="overflow-x-auto rounded-xl border border-slate-200 bg-white p-6">
              <h2 className="text-lg font-semibold text-navy-900">Departments</h2>
              <table className="mt-4 min-w-full text-left text-sm">
                <thead>
                  <tr className="border-b border-slate-200 text-xs uppercase tracking-wide text-slate-500">
                    <th className="py-2 pr-4 font-medium">Department</th>
                    <th className="py-2 font-medium">People</th>
                  </tr>
                </thead>
                <tbody>
                  {data.departments.map((row) => (
                    <tr key={row.department} className="border-b border-slate-100">
                      <td className="py-2 pr-4 font-medium text-navy-900">
                        {row.department}
                      </td>
                      <td className="py-2 text-slate-600">{row.employee_count}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </section>
          ) : null}
        </>
      ) : null}
    </div>
  );
}
