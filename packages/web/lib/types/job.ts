export type JobStatus = "queued" | "rendering" | "done" | "failed";

export interface Job {
  id: string;
  brief_id: string;
  status: JobStatus;
  composition: Record<string, unknown> | null;
  output_s3_key: string | null;
  render_duration_ms: number | null;
  error_message: string | null;
  celery_task_id: string | null;
  created_at: string;
  updated_at: string | null;
}

export interface JobCreate {
  status?: JobStatus;
  composition?: Record<string, unknown> | null;
}
