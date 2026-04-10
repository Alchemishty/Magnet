import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import type { Job, JobCreate } from "@/lib/types/job";

// Mock the client module before importing jobs
vi.mock("@/lib/api/client", () => ({
  apiGet: vi.fn(),
  apiPost: vi.fn(),
}));

import { apiGet, apiPost } from "@/lib/api/client";
import { createJob, listJobs, getJob } from "@/lib/api/jobs";

const mockJob: Job = {
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

beforeEach(() => {
  vi.clearAllMocks();
});

afterEach(() => {
  vi.restoreAllMocks();
});

describe("createJob", () => {
  it("calls apiPost with correct path and body", async () => {
    vi.mocked(apiPost).mockResolvedValue(mockJob);

    const data: JobCreate = { composition: { layers: [] } };
    const result = await createJob("brief-1", data);

    expect(apiPost).toHaveBeenCalledWith("/api/briefs/brief-1/jobs", data);
    expect(result).toEqual(mockJob);
  });

  it("calls apiPost with empty body when no data provided", async () => {
    vi.mocked(apiPost).mockResolvedValue(mockJob);

    const result = await createJob("brief-1");

    expect(apiPost).toHaveBeenCalledWith("/api/briefs/brief-1/jobs", {});
    expect(result).toEqual(mockJob);
  });
});

describe("listJobs", () => {
  it("calls apiGet with correct path when no filter", async () => {
    vi.mocked(apiGet).mockResolvedValue([mockJob]);

    const result = await listJobs("brief-1");

    expect(apiGet).toHaveBeenCalledWith("/api/briefs/brief-1/jobs");
    expect(result).toEqual([mockJob]);
  });

  it("calls apiGet with status query param when provided", async () => {
    vi.mocked(apiGet).mockResolvedValue([mockJob]);

    const result = await listJobs("brief-1", "rendering");

    expect(apiGet).toHaveBeenCalledWith(
      "/api/briefs/brief-1/jobs?status=rendering",
    );
    expect(result).toEqual([mockJob]);
  });
});

describe("getJob", () => {
  it("calls apiGet with correct path", async () => {
    vi.mocked(apiGet).mockResolvedValue(mockJob);

    const result = await getJob("job-1");

    expect(apiGet).toHaveBeenCalledWith("/api/jobs/job-1");
    expect(result).toEqual(mockJob);
  });
});
