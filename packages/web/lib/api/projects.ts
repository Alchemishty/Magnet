import type {
  Project,
  ProjectCreate,
  ProjectUpdate,
} from "@/lib/types/project";
import { apiGet, apiPost, apiPatch, apiDelete } from "./client";

export async function createProject(data: ProjectCreate): Promise<Project> {
  return apiPost<Project>("/api/projects", data);
}

export async function listProjects(
  userId: string,
  offset = 0,
  limit = 100,
): Promise<Project[]> {
  return apiGet<Project[]>(
    `/api/projects?user_id=${userId}&offset=${offset}&limit=${limit}`,
  );
}

export async function getProject(id: string): Promise<Project> {
  return apiGet<Project>(`/api/projects/${id}`);
}

export async function updateProject(
  id: string,
  data: ProjectUpdate,
): Promise<Project> {
  return apiPatch<Project>(`/api/projects/${id}`, data);
}

export async function deleteProject(id: string): Promise<void> {
  return apiDelete(`/api/projects/${id}`);
}
