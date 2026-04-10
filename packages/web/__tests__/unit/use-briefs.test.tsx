import { renderHook, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { vi, describe, it, expect, beforeEach } from "vitest";
import type { ReactNode } from "react";

import {
  useBriefs,
  useGenerateConcepts,
  useUpdateBrief,
  useDeleteBrief,
} from "@/lib/hooks/use-briefs";
import {
  listBriefs,
  generateConcepts,
  updateBrief,
  deleteBrief,
} from "@/lib/api/briefs";
import type { Brief } from "@/lib/types/brief";

vi.mock("@/lib/api/briefs", () => ({
  listBriefs: vi.fn(),
  generateConcepts: vi.fn(),
  updateBrief: vi.fn(),
  deleteBrief: vi.fn(),
}));

const mockBrief: Brief = {
  id: "brief-1",
  project_id: "proj-1",
  hook_type: "fail_challenge",
  narrative_angle: "Show difficulty then mastery",
  script: "Watch this impossible level...",
  voiceover_text: null,
  target_emotion: "excitement",
  cta_text: "Download now!",
  reference_ads: [],
  target_format: "9:16",
  target_duration: 30,
  status: "draft",
  generated_by: "concept_agent",
  scene_plan: null,
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

describe("useBriefs", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("fetches briefs for a given project", async () => {
    vi.mocked(listBriefs).mockResolvedValue([mockBrief]);

    const { result } = renderHook(() => useBriefs("proj-1"), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(listBriefs).toHaveBeenCalledWith("proj-1", undefined);
    expect(result.current.data).toEqual([mockBrief]);
  });

  it("passes status filter to listBriefs", async () => {
    vi.mocked(listBriefs).mockResolvedValue([mockBrief]);

    const { result } = renderHook(() => useBriefs("proj-1", "approved"), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(listBriefs).toHaveBeenCalledWith("proj-1", "approved");
  });

  it("does not fetch when projectId is empty", () => {
    const { result } = renderHook(() => useBriefs(""), {
      wrapper: createWrapper(),
    });

    expect(result.current.fetchStatus).toBe("idle");
    expect(listBriefs).not.toHaveBeenCalled();
  });
});

describe("useGenerateConcepts", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("calls generateConcepts with project id", async () => {
    vi.mocked(generateConcepts).mockResolvedValue([mockBrief]);

    const { result } = renderHook(() => useGenerateConcepts("proj-1"), {
      wrapper: createWrapper(),
    });

    result.current.mutate();

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(generateConcepts).toHaveBeenCalledWith("proj-1");
    expect(result.current.data).toEqual([mockBrief]);
  });
});

describe("useDeleteBrief", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("calls deleteBrief with correct id", async () => {
    vi.mocked(deleteBrief).mockResolvedValue(undefined);

    const { result } = renderHook(() => useDeleteBrief(), {
      wrapper: createWrapper(),
    });

    result.current.mutate("brief-1");

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(deleteBrief).toHaveBeenCalledWith("brief-1");
  });
});
