import { renderHook, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { vi, describe, it, expect, beforeEach } from "vitest";
import type { ReactNode } from "react";

import {
  useProjects,
  useProject,
  useCreateProject,
  useUpdateProject,
  useDeleteProject,
} from "@/lib/hooks/use-projects";
import {
  listProjects,
  getProject,
  createProject,
  updateProject,
  deleteProject,
} from "@/lib/api/projects";
import type { Project } from "@/lib/types/project";

vi.mock("@/lib/api/projects", () => ({
  listProjects: vi.fn(),
  getProject: vi.fn(),
  createProject: vi.fn(),
  updateProject: vi.fn(),
  deleteProject: vi.fn(),
}));

const mockProject: Project = {
  id: "proj-1",
  user_id: "user-1",
  name: "Test Project",
  status: "active",
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

describe("useProjects", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("fetches projects for a given user", async () => {
    vi.mocked(listProjects).mockResolvedValue([mockProject]);

    const { result } = renderHook(() => useProjects("user-1"), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(listProjects).toHaveBeenCalledWith("user-1");
    expect(result.current.data).toEqual([mockProject]);
  });

  it("returns error when listProjects fails", async () => {
    vi.mocked(listProjects).mockRejectedValue(new Error("Network error"));

    const { result } = renderHook(() => useProjects("user-1"), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isError).toBe(true));

    expect(result.current.error).toBeInstanceOf(Error);
  });
});

describe("useProject", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("fetches a single project by id", async () => {
    vi.mocked(getProject).mockResolvedValue(mockProject);

    const { result } = renderHook(() => useProject("proj-1"), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(getProject).toHaveBeenCalledWith("proj-1");
    expect(result.current.data).toEqual(mockProject);
  });

  it("does not fetch when id is empty", () => {
    const { result } = renderHook(() => useProject(""), {
      wrapper: createWrapper(),
    });

    expect(result.current.fetchStatus).toBe("idle");
    expect(getProject).not.toHaveBeenCalled();
  });
});

describe("useCreateProject", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("calls createProject with correct data", async () => {
    vi.mocked(createProject).mockResolvedValue(mockProject);

    const { result } = renderHook(() => useCreateProject(), {
      wrapper: createWrapper(),
    });

    result.current.mutate({ name: "Test Project", user_id: "user-1" });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(createProject).toHaveBeenCalledWith({
      name: "Test Project",
      user_id: "user-1",
    });
  });
});

describe("useUpdateProject", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("calls updateProject with id and data", async () => {
    vi.mocked(updateProject).mockResolvedValue({
      ...mockProject,
      name: "Updated",
    });

    const { result } = renderHook(() => useUpdateProject("proj-1"), {
      wrapper: createWrapper(),
    });

    result.current.mutate({ name: "Updated" });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(updateProject).toHaveBeenCalledWith("proj-1", { name: "Updated" });
  });
});

describe("useDeleteProject", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("calls deleteProject with correct id", async () => {
    vi.mocked(deleteProject).mockResolvedValue(undefined);

    const { result } = renderHook(() => useDeleteProject(), {
      wrapper: createWrapper(),
    });

    result.current.mutate("proj-1");

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(deleteProject).toHaveBeenCalledWith("proj-1");
  });
});
