import type { Job, JobCreate, JobStatus } from "@/lib/types/job";
import { apiGet, apiPost } from "./client";

export async function createJob(
  briefId: string,
  data?: JobCreate,
): Promise<Job> {
  return apiPost<Job>(`/api/briefs/${briefId}/jobs`, data ?? {});
}

export async function listJobs(
  briefId: string,
  status?: JobStatus,
): Promise<Job[]> {
  const params = new URLSearchParams();
  if (status) params.set("status", status);
  const query = params.toString();
  return apiGet<Job[]>(
    `/api/briefs/${briefId}/jobs${query ? `?${query}` : ""}`,
  );
}

export async function getJob(jobId: string): Promise<Job> {
  return apiGet<Job>(`/api/jobs/${jobId}`);
}
