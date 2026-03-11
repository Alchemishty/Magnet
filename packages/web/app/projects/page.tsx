"use client";

import Link from "next/link";
import { useProjects } from "@/lib/hooks/use-projects";
import { ProjectCard } from "@/components/project-card";
import { Button } from "@/components/ui/button";
import { STUB_USER_ID } from "@/lib/constants";

export default function ProjectsPage() {
  const { data: projects, isLoading, isError, error } = useProjects(STUB_USER_ID);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <p className="text-muted-foreground">Loading projects...</p>
      </div>
    );
  }

  if (isError) {
    return (
      <div className="flex items-center justify-center h-64">
        <p className="text-destructive">
          Failed to load projects: {error instanceof Error ? error.message : "Unknown error"}
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold">Projects</h1>
        <Link href="/projects/new">
          <Button>New Project</Button>
        </Link>
      </div>

      {projects && projects.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {projects.map((project) => (
            <ProjectCard key={project.id} project={project} />
          ))}
        </div>
      ) : (
        <div className="flex flex-col items-center justify-center h-64 space-y-4">
          <p className="text-muted-foreground">No projects yet.</p>
          <Link href="/projects/new">
            <Button>Create your first project</Button>
          </Link>
        </div>
      )}
    </div>
  );
}
