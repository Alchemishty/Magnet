import type { Brief, BriefStatus, BriefUpdate } from "@/lib/types/brief";
import { apiGet, apiPost, apiPatch, apiDelete } from "./client";

export async function generateConcepts(projectId: string): Promise<Brief[]> {
  return apiPost<Brief[]>(`/api/projects/${projectId}/concepts`, {});
}

export async function listBriefs(
  projectId: string,
  status?: BriefStatus,
): Promise<Brief[]> {
  const params = new URLSearchParams();
  if (status) params.set("status", status);
  const query = params.toString();
  return apiGet<Brief[]>(
    `/api/projects/${projectId}/briefs${query ? `?${query}` : ""}`,
  );
}

export async function getBrief(briefId: string): Promise<Brief> {
  return apiGet<Brief>(`/api/briefs/${briefId}`);
}

export async function updateBrief(
  briefId: string,
  data: BriefUpdate,
): Promise<Brief> {
  return apiPatch<Brief>(`/api/briefs/${briefId}`, data);
}

export async function deleteBrief(briefId: string): Promise<void> {
  return apiDelete(`/api/briefs/${briefId}`);
}
