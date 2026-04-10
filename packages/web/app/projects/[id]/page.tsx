"use client";

import { useParams } from "next/navigation";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { GameProfileForm } from "@/components/game-profile-form";
import { AssetUpload } from "@/components/asset-upload";
import { useProject } from "@/lib/hooks/use-projects";

export default function ProjectDetailPage() {
  const params = useParams<{ id: string }>();
  const { data: project, isLoading, isError } = useProject(params.id);

  if (isLoading) {
    return <p className="text-muted-foreground">Loading project...</p>;
  }

  if (isError || !project) {
    return <p className="text-destructive">Project not found.</p>;
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <h1 className="text-3xl font-bold">{project.name}</h1>
        <Badge variant="secondary">{project.status}</Badge>
      </div>
      <GameProfileForm projectId={project.id} />
      <Separator />
      <AssetUpload projectId={project.id} />
    </div>
  );
}
