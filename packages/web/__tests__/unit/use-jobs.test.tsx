import { renderHook, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { vi, describe, it, expect, beforeEach } from "vitest";
import type { ReactNode } from "react";

import { useJobs, useJob, useCreateJob } from "@/lib/hooks/use-jobs";
import { listJobs, getJob, createJob } from "@/lib/api/jobs";
import type { Job } from "@/lib/types/job";

vi.mock("@/lib/api/jobs", () => ({
  listJobs: vi.fn(),
  getJob: vi.fn(),
  createJob: vi.fn(),
}));

const mockJob: Job = {
  id: "job-1",
  brief_id: "brief-1",
  status: "queued",
  composition: null,
  output_s3_key: null,
  render_duration_ms: null,
  error_message: null,
  celery_task_id: null,
  created_at: "2026-01-01T00:00:00Z",
  updated_at: null,
};

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  function Wrapper({ children }: { children: ReactNode }) {
    return (
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    );
  }
  return Wrapper;
}

describe("useJobs", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("fetches jobs for a given brief", async () => {
    vi.mocked(listJobs).mockResolvedValue([mockJob]);

    const { result } = renderHook(() => useJobs("brief-1"), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(listJobs).toHaveBeenCalledWith("brief-1");
    expect(result.current.data).toEqual([mockJob]);
  });

  it("does not fetch when briefId is empty", () => {
    const { result } = renderHook(() => useJobs(""), {
      wrapper: createWrapper(),
    });

    expect(result.current.fetchStatus).toBe("idle");
    expect(listJobs).not.toHaveBeenCalled();
  });
});

describe("useJob", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("fetches a single job by id", async () => {
    vi.mocked(getJob).mockResolvedValue(mockJob);

    const { result } = renderHook(() => useJob("job-1"), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(getJob).toHaveBeenCalledWith("job-1");
    expect(result.current.data).toEqual(mockJob);
  });

  it("does not fetch when jobId is empty", () => {
    const { result } = renderHook(() => useJob(""), {
      wrapper: createWrapper(),
    });

    expect(result.current.fetchStatus).toBe("idle");
    expect(getJob).not.toHaveBeenCalled();
  });
});

describe("useCreateJob", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("calls createJob with correct briefId", async () => {
    vi.mocked(createJob).mockResolvedValue(mockJob);

    const { result } = renderHook(() => useCreateJob("brief-1"), {
      wrapper: createWrapper(),
    });

    result.current.mutate();

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(createJob).toHaveBeenCalledWith("brief-1", undefined);
    expect(result.current.data).toEqual(mockJob);
  });

  it("passes JobCreate data to createJob", async () => {
    vi.mocked(createJob).mockResolvedValue(mockJob);

    const { result } = renderHook(() => useCreateJob("brief-1"), {
      wrapper: createWrapper(),
    });

    result.current.mutate({ status: "queued", composition: { layers: [] } });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(createJob).toHaveBeenCalledWith("brief-1", {
      status: "queued",
      composition: { layers: [] },
    });
  });
});
