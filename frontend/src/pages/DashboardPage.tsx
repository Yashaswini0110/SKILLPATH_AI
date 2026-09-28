import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { fetchProfile } from "../services/auth";
import { useAuthStore } from "../store/authStore";

const ANALYTICS_ROLES = new Set(["MANAGER", "HR_ADMIN", "SYSTEM_ADMIN"]);

export function DashboardPage() {
  const user = useAuthStore((state) => state.user);
  const profileQuery = useQuery({ queryKey: ["profile"], queryFn: fetchProfile });
  const profile = profileQuery.data;
  const completeness = profile ? Math.round(profile.completeness.score * 100) : 0;
  const showAnalytics = ANALYTICS_ROLES.has(user?.role ?? "");

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold text-navy-900">Welcome, {user?.full_name}</h1>

      <dl className="grid gap-4 md:grid-cols-3">
        <Stat label="Profile" value={`${completeness}%`} />
        <Stat label="Target" value={profile?.target_role?.title ?? "Not selected"} />
        <Stat label="Skills" value={String(profile?.skills.length ?? 0)} />
      </dl>

      <section className="rounded-xl border border-slate-200 bg-white p-6">
        <div className="flex flex-wrap gap-2">
          <StartLink to="/profile" label="Profile" />
          <StartLink to="/gaps" label="Gaps" />
          <StartLink to="/path" label="Path" />
          <StartLink to="/recommendations" label="Recommend" />
          {showAnalytics ? <StartLink to="/analytics" label="Analytics" /> : null}
        </div>
      </section>
    </div>
  );
}

function StartLink({ to, label }: { to: string; label: string }) {
  return (
    <Link
      to={to}
      className="rounded-lg border border-slate-200 px-4 py-2 text-sm font-medium text-navy-800 hover:bg-slate-50"
    >
      {label}
    </Link>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-5">
      <dt className="text-xs uppercase tracking-wide text-slate-500">{label}</dt>
      <dd className="mt-2 text-xl font-semibold text-navy-900">{value}</dd>
    </div>
  );
}
