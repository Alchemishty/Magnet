import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { JobCard } from "@/components/job-card";
import type { Job } from "@/lib/types/job";

const baseJob: Job = {
  id: "job-1",
  brief_id: "brief-1",
  status: "queued",
  composition: null,
  output_s3_key: null,
  render_duration_ms: null,
  error_message: null,
  celery_task_id: null,
  created_at: "2026-04-10T00:00:00Z",
  updated_at: null,
};

describe("JobCard", () => {
  it("renders queued status", () => {
    render(<JobCard job={baseJob} />);
    expect(screen.getByText("queued")).toBeInTheDocument();
    expect(screen.getByText(/waiting/i)).toBeInTheDocument();
  });

  it("renders rendering status with progress", () => {
    const job = { ...baseJob, status: "rendering" as const };
    const progress = {
      job_id: "job-1",
      brief_id: "brief-1",
      status: "rendering" as const,
      phase: "PREPARE",
      progress_pct: 40,
      message: "Preparing assets",
      timestamp: "2026-04-10T00:01:00Z",
    };
    render(<JobCard job={job} progress={progress} />);
    expect(screen.getByText("rendering")).toBeInTheDocument();
    expect(screen.getByText(/PREPARE/)).toBeInTheDocument();
    expect(screen.getByText(/40%/)).toBeInTheDocument();
  });

  it("renders done status with duration", () => {
    const job = { ...baseJob, status: "done" as const, render_duration_ms: 12300 };
    render(<JobCard job={job} />);
    expect(screen.getByText("done")).toBeInTheDocument();
    expect(screen.getByText(/12\.3s/)).toBeInTheDocument();
  });

  it("renders failed status with error message", () => {
    const job = { ...baseJob, status: "failed" as const, error_message: "FFmpeg crashed" };
    render(<JobCard job={job} />);
    expect(screen.getByText("failed")).toBeInTheDocument();
    expect(screen.getByText(/FFmpeg crashed/)).toBeInTheDocument();
  });
});
