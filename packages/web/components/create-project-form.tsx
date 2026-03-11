"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { useCreateProject } from "@/lib/hooks/use-projects";
import { STUB_USER_ID } from "@/lib/constants";

export function CreateProjectForm() {
  const [name, setName] = useState("");
  const router = useRouter();
  const createProject = useCreateProject();

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) return;
    createProject.mutate(
      { name: name.trim(), user_id: STUB_USER_ID },
      {
        onSuccess: (project) => {
          router.push(`/projects/${project.id}`);
        },
      }
    );
  };

  return (
    <Card className="max-w-lg">
      <CardHeader>
        <CardTitle>Create New Project</CardTitle>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="project-name">Project Name</Label>
            <Input
              id="project-name"
              placeholder="My Game"
              value={name}
              onChange={(e) => setName(e.target.value)}
              required
            />
          </div>
          <Button
            type="submit"
            disabled={createProject.isPending || !name.trim()}
          >
            {createProject.isPending ? "Creating..." : "Create Project"}
          </Button>
          {createProject.isError && (
            <p className="text-sm text-destructive">
              Failed to create project. Please try again.
            </p>
          )}
        </form>
      </CardContent>
    </Card>
  );
}
