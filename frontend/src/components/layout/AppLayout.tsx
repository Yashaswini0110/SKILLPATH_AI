import { useState } from "react";
import { Outlet, useLocation, useNavigate } from "react-router-dom";
import { LogOut, Menu, X } from "lucide-react";
import { useAuthStore } from "../../store/authStore";
import { logoutAccount } from "../../services/auth";
import { AppNav, titleForPath } from "./AppNav";

export function AppLayout() {
  const user = useAuthStore((state) => state.user);
  const refreshToken = useAuthStore((state) => state.refreshToken);
  const logout = useAuthStore((state) => state.logout);
  const navigate = useNavigate();
  const { pathname } = useLocation();
  const [menuOpen, setMenuOpen] = useState(false);

  async function handleLogout() {
    try {
      await logoutAccount(refreshToken);
    } catch {
      // Local logout still proceeds.
    }
    logout();
    navigate("/login");
  }

  return (
    <div className="min-h-screen bg-slate-50 lg:grid lg:grid-cols-[240px_1fr]">
      <a
        href="#main"
        className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-4 focus:z-50 focus:rounded-md focus:bg-white focus:px-3 focus:py-2 focus:text-sm focus:text-navy-900"
      >
        Skip to content
      </a>
      {menuOpen ? (
        <button
          type="button"
          className="fixed inset-0 z-30 bg-navy-900/40 lg:hidden"
          aria-label="Close menu"
          onClick={() => setMenuOpen(false)}
        />
      ) : null}
      <aside
        className={[
          "fixed inset-y-0 left-0 z-40 flex w-64 max-h-screen flex-col bg-navy-900 text-white transition-transform lg:static lg:w-auto lg:translate-x-0",
          menuOpen ? "translate-x-0" : "-translate-x-full lg:translate-x-0",
        ].join(" ")}
      >
        <div className="flex h-16 shrink-0 items-center justify-between border-b border-white/10 px-6">
          <div>
            <p className="text-sm font-semibold tracking-wide">SkillPath AI</p>
          </div>
          <button
            type="button"
            className="rounded-md p-1 text-slate-300 hover:bg-white/10 lg:hidden"
            aria-label="Close menu"
            onClick={() => setMenuOpen(false)}
          >
            <X size={18} />
          </button>
        </div>
        <AppNav onNavigate={() => setMenuOpen(false)} />
        <div className="border-t border-white/10 px-4 py-4">
          <p className="truncate px-3 text-xs text-slate-400">{user?.full_name}</p>
          <p className="px-3 text-xs text-slate-500">{user?.role}</p>
        </div>
      </aside>
      <div className="flex min-h-screen flex-col">
        <header className="flex h-16 items-center justify-between border-b border-slate-200 bg-white px-4 sm:px-6">
          <div className="flex items-center gap-3">
            <button
              type="button"
              className="rounded-md border border-slate-200 p-2 text-slate-700 hover:bg-slate-50 lg:hidden"
              aria-label="Open menu"
              aria-expanded={menuOpen}
              onClick={() => setMenuOpen(true)}
            >
              <Menu size={18} />
            </button>
            <p className="text-sm font-medium text-slate-600">{titleForPath(pathname)}</p>
          </div>
          <button
            type="button"
            onClick={() => void handleLogout()}
            className="inline-flex items-center gap-2 rounded-md border border-slate-200 px-3 py-1.5 text-sm text-slate-700 hover:bg-slate-50 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-navy-700"
          >
            <LogOut size={14} aria-hidden />
            Sign out
          </button>
        </header>
        <main id="main" className="flex-1 p-4 sm:p-6" tabIndex={-1}>
          <Outlet />
        </main>
      </div>
    </div>
  );
}
