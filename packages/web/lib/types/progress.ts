export interface ProgressEvent {
  job_id: string;
  brief_id: string;
  status: "queued" | "rendering" | "done" | "failed" | "phase_update";
  phase: string | null;
  progress_pct: number | null;
  message: string | null;
  timestamp: string;
}
