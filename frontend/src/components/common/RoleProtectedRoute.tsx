import { useEffect, useState } from "react";
import { Link, Outlet } from "react-router-dom";
import { useAuthStore } from "../../store/authStore";
import type { UserRole } from "../../types/api";

const ALLOWED: UserRole[] = ["MANAGER", "HR_ADMIN", "SYSTEM_ADMIN"];

export function RoleProtectedRoute() {
  const role = useAuthStore((state) => state.user?.role);
  const [ready, setReady] = useState(() => useAuthStore.persist.hasHydrated());

  useEffect(() => {
    if (ready) {
      return;
    }
    return useAuthStore.persist.onFinishHydration(() => setReady(true));
  }, [ready]);

  if (!ready) {
    return <p className="text-sm text-slate-500">Checking access…</p>;
  }

  if (!role || !ALLOWED.includes(role)) {
    return (
      <div className="space-y-3">
        <h1 className="text-2xl font-semibold text-navy-900">Analytics</h1>
        <p className="text-sm text-slate-600">
          This page is for managers and HR. It shows department or org counts only,
          not individual names. Sign in with a manager or HR admin account, and set
          a department on the manager profile.
        </p>
        <Link to="/dashboard" className="text-sm text-teal-700 hover:underline">
          Back to dashboard
        </Link>
      </div>
    );
  }

  return <Outlet />;
}
