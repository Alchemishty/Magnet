import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";

import {
  listProjects,
  getProject,
  createProject,
  updateProject,
  deleteProject,
} from "@/lib/api/projects";
import type { ProjectCreate, ProjectUpdate } from "@/lib/types/project";

export function useProjects(userId: string) {
  return useQuery({
    queryKey: ["projects", "list", userId],
    queryFn: () => listProjects(userId),
  });
}

export function useProject(id: string) {
  return useQuery({
    queryKey: ["projects", "detail", id],
    queryFn: () => getProject(id),
    enabled: !!id,
  });
}

export function useCreateProject() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: ProjectCreate) => createProject(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["projects"] });
    },
  });
}

export function useUpdateProject(id: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: ProjectUpdate) => updateProject(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["projects"] });
    },
  });
}

export function useDeleteProject() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => deleteProject(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["projects"] });
    },
  });
}
