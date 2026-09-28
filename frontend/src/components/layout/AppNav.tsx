import { useEffect, useState, type ReactNode } from "react";
import { NavLink, useLocation } from "react-router-dom";
import {
  BarChart3,
  BookOpen,
  Briefcase,
  ChartNoAxesCombined,
  ChevronDown,
  ClipboardCheck,
  FileUp,
  Layers,
  LayoutDashboard,
  ListOrdered,
  MessageCircle,
  Scale,
  Shield,
  Sparkles,
  UserRound,
  Users,
} from "lucide-react";
import { useAuthStore } from "../../store/authStore";

const ANALYTICS_ROLES = new Set(["MANAGER", "HR_ADMIN", "SYSTEM_ADMIN"]);

const linkClass = ({ isActive }: { isActive: boolean }) =>
  [
    "flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-white",
    isActive ? "bg-white/10 text-white" : "text-slate-300 hover:bg-white/5 hover:text-white",
  ].join(" ");

export function AppNav({ onNavigate }: { onNavigate?: () => void }) {
  const role = useAuthStore((state) => state.user?.role);

  return (
    <nav className="flex-1 space-y-1 overflow-y-auto p-4" aria-label="Main">
      <NavLink to="/dashboard" className={linkClass} onClick={onNavigate} end>
        <LayoutDashboard size={16} aria-hidden />
        Home
      </NavLink>

      <NavGroup title="You" paths={["/profile", "/resume"]}>
        <NavLink to="/profile" className={linkClass} onClick={onNavigate}>
          <UserRound size={16} aria-hidden />
          Profile
        </NavLink>
        <NavLink to="/resume" className={linkClass} onClick={onNavigate}>
          <FileUp size={16} aria-hidden />
          Resume
        </NavLink>
      </NavGroup>

      <NavGroup title="Skills" paths={["/skills", "/gaps"]}>
        <NavLink to="/skills" className={linkClass} onClick={onNavigate}>
          <Shield size={16} aria-hidden />
          Overview
        </NavLink>
        <NavLink to="/gaps" className={linkClass} onClick={onNavigate}>
          <BarChart3 size={16} aria-hidden />
          Gaps
        </NavLink>
      </NavGroup>

      <NavGroup
        title="Learn"
        paths={["/path", "/recommendations", "/practice", "/mentors", "/assessments", "/resources"]}
      >
        <NavLink to="/path" className={linkClass} onClick={onNavigate}>
          <ListOrdered size={16} aria-hidden />
          Path
        </NavLink>
        <NavLink to="/recommendations" className={linkClass} onClick={onNavigate}>
          <Sparkles size={16} aria-hidden />
          Recommend
        </NavLink>
        <NavLink to="/practice" className={linkClass} onClick={onNavigate}>
          <Layers size={16} aria-hidden />
          Practice
        </NavLink>
        <NavLink to="/mentors" className={linkClass} onClick={onNavigate}>
          <Users size={16} aria-hidden />
          Mentors
        </NavLink>
        <NavLink to="/assessments" className={linkClass} onClick={onNavigate}>
          <ClipboardCheck size={16} aria-hidden />
          Assess
        </NavLink>
        <NavLink to="/resources" className={linkClass} onClick={onNavigate}>
          <BookOpen size={16} aria-hidden />
          Catalog
        </NavLink>
      </NavGroup>

      <NavLink to="/assistant" className={linkClass} onClick={onNavigate}>
        <MessageCircle size={16} aria-hidden />
        Assistant
      </NavLink>

      <NavGroup title="Explore" paths={["/compare", "/roles"]}>
        <NavLink to="/compare" className={linkClass} onClick={onNavigate}>
          <Scale size={16} aria-hidden />
          Compare
        </NavLink>
        <NavLink to="/roles" className={linkClass} onClick={onNavigate}>
          <Briefcase size={16} aria-hidden />
          Roles
        </NavLink>
      </NavGroup>

      {ANALYTICS_ROLES.has(role ?? "") ? (
        <NavLink to="/analytics" className={linkClass} onClick={onNavigate}>
          <ChartNoAxesCombined size={16} aria-hidden />
          Analytics
        </NavLink>
      ) : null}
    </nav>
  );
}

function NavGroup({
  title,
  paths,
  children,
}: {
  title: string;
  paths: string[];
  children: ReactNode;
}) {
  const { pathname } = useLocation();
  const childActive = paths.some(
    (path) => pathname === path || pathname.startsWith(`${path}/`),
  );
  const [open, setOpen] = useState(childActive);

  useEffect(() => {
    if (childActive) {
      setOpen(true);
    }
  }, [childActive]);

  const panelId = `nav-${title.toLowerCase()}`;

  return (
    <div>
      <button
        type="button"
        className="flex w-full items-center justify-between rounded-lg px-3 py-2 text-left text-xs font-semibold uppercase tracking-wide text-slate-400 hover:bg-white/5 hover:text-slate-200 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-white"
        aria-expanded={open}
        aria-controls={panelId}
        onClick={() => setOpen((value) => !value)}
      >
        {title}
        <ChevronDown
          size={14}
          aria-hidden
          className={open ? "rotate-180 transition" : "transition"}
        />
      </button>
      {open ? (
        <div id={panelId} className="mt-1 space-y-1 pl-2">
          {children}
        </div>
      ) : null}
    </div>
  );
}

export const PAGE_TITLES: Record<string, string> = {
  "/dashboard": "Home",
  "/profile": "Profile",
  "/resume": "Resume",
  "/skills": "Skill profile",
  "/gaps": "Skill gaps",
  "/path": "Learning path",
  "/recommendations": "Recommendations",
  "/practice": "Practice",
  "/mentors": "Mentors",
  "/assessments": "Assessments",
  "/resources": "Catalog",
  "/assistant": "Assistant",
  "/compare": "Compare roles",
  "/roles": "Roles",
  "/analytics": "Analytics",
};

export function titleForPath(pathname: string): string {
  if (pathname.startsWith("/assessments/")) {
    return "Quiz";
  }
  return PAGE_TITLES[pathname] ?? "SkillPath AI";
}
