"use client";
import { useState } from "react";
import { Navbar } from "./navbar";
import { Sidebar } from "./sidebar";

export function Shell({ children }: { children: React.ReactNode }) {
  const [navOpen, setNavOpen] = useState(false);

  return (
    <div className="flex h-screen bg-zinc-950 text-zinc-100 overflow-hidden">
      <Sidebar open={navOpen} onClose={() => setNavOpen(false)} />
      <div className="flex-1 flex flex-col min-w-0">
        <Navbar onMenuClick={() => setNavOpen(true)} />
        <main className="flex-1 overflow-y-auto p-4 sm:p-6 space-y-6">
          {children}
        </main>
      </div>
    </div>
  );
}
