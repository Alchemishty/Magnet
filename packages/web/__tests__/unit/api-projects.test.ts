import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import type { Project } from "@/lib/types/project";

// Mock the client module before importing projects
vi.mock("@/lib/api/client", () => ({
  apiGet: vi.fn(),
  apiPost: vi.fn(),
  apiPatch: vi.fn(),
  apiDelete: vi.fn(),
}));

import { apiGet, apiPost, apiPatch, apiDelete } from "@/lib/api/client";
import {
  createProject,
  listProjects,
  getProject,
  updateProject,
  deleteProject,
} from "@/lib/api/projects";

const mockProject: Project = {
  id: "proj-1",
  user_id: "user-1",
  name: "Test Project",
  status: "active",
  created_at: "2026-03-11T00:00:00Z",
  updated_at: null,
};

beforeEach(() => {
  vi.clearAllMocks();
});

afterEach(() => {
  vi.restoreAllMocks();
});

describe("createProject", () => {
  it("calls apiPost with /api/projects and body", async () => {
    vi.mocked(apiPost).mockResolvedValue(mockProject);

    const body = { name: "Test Project", user_id: "user-1" };
    const result = await createProject(body);

    expect(apiPost).toHaveBeenCalledWith("/api/projects", body);
    expect(result).toEqual(mockProject);
  });
});

describe("listProjects", () => {
  it("calls apiGet with correct query params using defaults", async () => {
    vi.mocked(apiGet).mockResolvedValue([mockProject]);

    const result = await listProjects("user-1");

    expect(apiGet).toHaveBeenCalledWith(
      "/api/projects?user_id=user-1&offset=0&limit=100",
    );
    expect(result).toEqual([mockProject]);
  });

  it("calls apiGet with custom offset and limit", async () => {
    vi.mocked(apiGet).mockResolvedValue([]);

    await listProjects("user-1", 10, 25);

    expect(apiGet).toHaveBeenCalledWith(
      "/api/projects?user_id=user-1&offset=10&limit=25",
    );
  });
});

describe("getProject", () => {
  it("calls apiGet with /api/projects/{id}", async () => {
    vi.mocked(apiGet).mockResolvedValue(mockProject);

    const result = await getProject("proj-1");

    expect(apiGet).toHaveBeenCalledWith("/api/projects/proj-1");
    expect(result).toEqual(mockProject);
  });
});

describe("updateProject", () => {
  it("calls apiPatch with /api/projects/{id} and body", async () => {
    const updated = { ...mockProject, name: "Updated" };
    vi.mocked(apiPatch).mockResolvedValue(updated);

    const result = await updateProject("proj-1", { name: "Updated" });

    expect(apiPatch).toHaveBeenCalledWith("/api/projects/proj-1", {
      name: "Updated",
    });
    expect(result).toEqual(updated);
  });
});

describe("deleteProject", () => {
  it("calls apiDelete with /api/projects/{id}", async () => {
    vi.mocked(apiDelete).mockResolvedValue(undefined);

    await deleteProject("proj-1");

    expect(apiDelete).toHaveBeenCalledWith("/api/projects/proj-1");
  });
});
