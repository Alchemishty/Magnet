import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import type { Brief, BriefUpdate } from "@/lib/types/brief";

// Mock the client module before importing briefs
vi.mock("@/lib/api/client", () => ({
  apiGet: vi.fn(),
  apiPost: vi.fn(),
  apiPatch: vi.fn(),
  apiDelete: vi.fn(),
}));

import { apiGet, apiPost, apiPatch, apiDelete } from "@/lib/api/client";
import {
  generateConcepts,
  listBriefs,
  getBrief,
  updateBrief,
  deleteBrief,
} from "@/lib/api/briefs";

const mockBrief: Brief = {
  id: "brief-1",
  project_id: "proj-1",
  hook_type: "fail_challenge",
  narrative_angle: "Show the player failing then succeeding",
  script: "Watch me fail... then crush it!",
  voiceover_text: "Can you beat this level?",
  target_emotion: "excitement",
  cta_text: "Download now",
  reference_ads: [],
  target_format: "9:16",
  target_duration: 30,
  status: "draft",
  generated_by: "concept_agent",
  scene_plan: null,
  created_at: "2026-04-10T00:00:00Z",
  updated_at: null,
};

beforeEach(() => {
  vi.clearAllMocks();
});

afterEach(() => {
  vi.restoreAllMocks();
});

describe("generateConcepts", () => {
  it("calls apiPost with correct path and empty body", async () => {
    vi.mocked(apiPost).mockResolvedValue([mockBrief]);

    const result = await generateConcepts("proj-1");

    expect(apiPost).toHaveBeenCalledWith(
      "/api/projects/proj-1/concepts",
      {},
    );
    expect(result).toEqual([mockBrief]);
  });
});

describe("listBriefs", () => {
  it("calls apiGet with correct path when no filter", async () => {
    vi.mocked(apiGet).mockResolvedValue([mockBrief]);

    const result = await listBriefs("proj-1");

    expect(apiGet).toHaveBeenCalledWith("/api/projects/proj-1/briefs");
    expect(result).toEqual([mockBrief]);
  });

  it("calls apiGet with status query param when provided", async () => {
    vi.mocked(apiGet).mockResolvedValue([mockBrief]);

    const result = await listBriefs("proj-1", "draft");

    expect(apiGet).toHaveBeenCalledWith(
      "/api/projects/proj-1/briefs?status=draft",
    );
    expect(result).toEqual([mockBrief]);
  });
});

describe("getBrief", () => {
  it("calls apiGet with correct path", async () => {
    vi.mocked(apiGet).mockResolvedValue(mockBrief);

    const result = await getBrief("brief-1");

    expect(apiGet).toHaveBeenCalledWith("/api/briefs/brief-1");
    expect(result).toEqual(mockBrief);
  });
});

describe("updateBrief", () => {
  it("calls apiPatch with correct path and body", async () => {
    const updated = { ...mockBrief, status: "approved" as const };
    vi.mocked(apiPatch).mockResolvedValue(updated);

    const data: BriefUpdate = { status: "approved" };
    const result = await updateBrief("brief-1", data);

    expect(apiPatch).toHaveBeenCalledWith("/api/briefs/brief-1", data);
    expect(result).toEqual(updated);
  });
});

describe("deleteBrief", () => {
  it("calls apiDelete with correct path", async () => {
    vi.mocked(apiDelete).mockResolvedValue(undefined);

    await deleteBrief("brief-1");

    expect(apiDelete).toHaveBeenCalledWith("/api/briefs/brief-1");
  });
});
