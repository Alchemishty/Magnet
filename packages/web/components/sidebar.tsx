"use client";

import Link from "next/link";
import { FolderKanban, Film, Settings } from "lucide-react";
import { Separator } from "@/components/ui/separator";

export function Sidebar() {
  return (
    <aside className="flex h-full w-64 flex-col bg-card text-card-foreground">
      {/* Branding */}
      <div className="px-6 py-5">
        <span className="text-xl font-bold tracking-tight">Magnet</span>
      </div>

      <Separator />

      {/* Navigation */}
      <nav className="flex-1 space-y-1 px-3 py-4">
        {/* Projects — active link */}
        <Link
          href="/projects"
          className="flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors hover:bg-accent hover:text-accent-foreground"
        >
          <FolderKanban className="h-4 w-4" />
          Projects
        </Link>

        {/* Creative Library — disabled / coming soon */}
        <div className="flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium text-muted-foreground cursor-not-allowed">
          <Film className="h-4 w-4" />
          Creative Library
          <span className="ml-auto text-xs">Soon</span>
        </div>

        {/* Settings — disabled / coming soon */}
        <div className="flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium text-muted-foreground cursor-not-allowed">
          <Settings className="h-4 w-4" />
          Settings
          <span className="ml-auto text-xs">Soon</span>
        </div>
      </nav>

      <Separator />

      {/* User avatar stub */}
      <div className="flex items-center gap-3 px-6 py-4">
        <div className="flex h-8 w-8 items-center justify-center rounded-full bg-muted text-sm font-medium">
          U
        </div>
      </div>
    </aside>
  );
}
