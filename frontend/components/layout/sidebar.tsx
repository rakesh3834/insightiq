"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { LayoutDashboard, Bot, BarChart3, Star, FlaskConical, FileText, Settings, AlertTriangle, Brain, X } from "lucide-react";
import { cn } from "@/lib/utils";

const ICONS: Record<string, React.ElementType> = {
  LayoutDashboard, Bot, BarChart3, Star, FlaskConical, FileText, Settings, AlertTriangle, Brain,
};

const NAV = [
  { label: "Dashboard", href: "/dashboard", icon: "LayoutDashboard" },
  { label: "AI Assistant", href: "/ai-assistant", icon: "Bot" },
  { label: "Analytics", href: "/analytics", icon: "BarChart3" },
  { label: "Reviews", href: "/reviews", icon: "Star" },
  { label: "Experiments", href: "/experiments", icon: "FlaskConical" },
  { label: "Risk Model", href: "/risk-model", icon: "Brain" },
  { label: "Reports", href: "/reports", icon: "FileText" },
];

const BOTTOM_NAV = [
  { label: "Settings", href: "/settings", icon: "Settings" },
];

// Shared nav body rendered by both the desktop rail and the mobile drawer.
// `onNavigate` closes the drawer when a link is tapped on mobile.
function SidebarBody({ onNavigate }: { onNavigate?: () => void }) {
  const pathname = usePathname();

  return (
    <>
      <nav className="flex-1 px-3 py-4 space-y-0.5 overflow-y-auto">
        <p className="text-[10px] font-semibold text-zinc-600 uppercase tracking-widest px-3 mb-3">Navigation</p>
        {NAV.map((item) => {
          const Icon = ICONS[item.icon];
          const active = pathname.startsWith(item.href);
          return (
            <Link
              key={item.href}
              href={item.href}
              onClick={onNavigate}
              className={cn(
                "flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-all group",
                active
                  ? "bg-indigo-600/15 text-indigo-400 border border-indigo-500/20"
                  : "text-zinc-500 hover:text-zinc-200 hover:bg-zinc-800/60"
              )}
            >
              <Icon className={cn("w-4 h-4 shrink-0", active ? "text-indigo-400" : "text-zinc-600 group-hover:text-zinc-400")} />
              {item.label}
              {item.label === "AI Assistant" && (
                <span className="ml-auto text-[9px] bg-indigo-600/20 text-indigo-400 border border-indigo-500/20 px-1.5 py-0.5 rounded-full font-medium">AI</span>
              )}
            </Link>
          );
        })}
      </nav>

      <div className="px-3 py-4 border-t border-zinc-800 space-y-0.5">
        {BOTTOM_NAV.map((item) => {
          const Icon = ICONS[item.icon];
          const active = pathname.startsWith(item.href);
          return (
            <Link
              key={item.href}
              href={item.href}
              onClick={onNavigate}
              className={cn(
                "flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-all",
                active ? "bg-indigo-600/15 text-indigo-400" : "text-zinc-500 hover:text-zinc-200 hover:bg-zinc-800/60"
              )}
            >
              <Icon className="w-4 h-4 shrink-0" />
              {item.label}
            </Link>
          );
        })}

        {/* User info */}
        <div className="flex items-center gap-3 px-3 py-2 mt-2">
          <div className="w-6 h-6 rounded-full bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center text-[10px] font-bold text-white shrink-0">R</div>
          <div className="min-w-0">
            <p className="text-xs font-medium text-zinc-300 truncate">Rakesh</p>
            <p className="text-[10px] text-zinc-600 truncate">Admin</p>
          </div>
        </div>
      </div>
    </>
  );
}

export function Sidebar({ open, onClose }: { open: boolean; onClose: () => void }) {
  return (
    <>
      {/* Desktop rail — static, visible from md up */}
      <aside className="hidden md:flex w-56 shrink-0 border-r border-zinc-800 bg-zinc-950 flex-col h-full">
        <SidebarBody />
      </aside>

      {/* Mobile backdrop */}
      <div
        aria-hidden
        onClick={onClose}
        className={cn(
          "fixed inset-0 z-50 bg-black/60 backdrop-blur-sm transition-opacity duration-200 md:hidden",
          open ? "opacity-100" : "opacity-0 pointer-events-none"
        )}
      />

      {/* Mobile drawer — slides in from the left */}
      <aside
        className={cn(
          "fixed inset-y-0 left-0 z-50 w-64 border-r border-zinc-800 bg-zinc-950 flex flex-col h-full transition-transform duration-200 md:hidden",
          open ? "translate-x-0" : "-translate-x-full"
        )}
      >
        <div className="flex items-center justify-between h-14 px-4 border-b border-zinc-800 shrink-0">
          <span className="font-semibold text-sm text-zinc-100 tracking-tight">InsightIQ</span>
          <button onClick={onClose} aria-label="Close menu" className="p-1.5 -mr-1.5 text-zinc-400 hover:text-zinc-100 rounded-lg hover:bg-zinc-800/60 transition-colors">
            <X className="w-5 h-5" />
          </button>
        </div>
        <SidebarBody onNavigate={onClose} />
      </aside>
    </>
  );
}
