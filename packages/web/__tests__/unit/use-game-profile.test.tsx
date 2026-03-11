import { renderHook, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { vi, describe, it, expect, beforeEach } from "vitest";
import type { ReactNode } from "react";

import {
  useGameProfile,
  useCreateGameProfile,
  useUpdateGameProfile,
} from "@/lib/hooks/use-game-profile";
import {
  getGameProfile,
  createGameProfile,
  updateGameProfile,
} from "@/lib/api/game-profiles";
import type { GameProfile } from "@/lib/types/game-profile";

vi.mock("@/lib/api/game-profiles", () => ({
  getGameProfile: vi.fn(),
  createGameProfile: vi.fn(),
  updateGameProfile: vi.fn(),
}));

const mockProfile: GameProfile = {
  id: "gp-1",
  project_id: "proj-1",
  genre: "puzzle",
  target_audience: "casual gamers",
  core_mechanics: ["match-3"],
  art_style: "cartoon",
  brand_guidelines: null,
  competitors: null,
  key_selling_points: ["relaxing"],
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

describe("useGameProfile", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("fetches game profile for a project", async () => {
    vi.mocked(getGameProfile).mockResolvedValue(mockProfile);

    const { result } = renderHook(() => useGameProfile("proj-1"), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(getGameProfile).toHaveBeenCalledWith("proj-1");
    expect(result.current.data).toEqual(mockProfile);
  });

  it("does not fetch when projectId is empty", () => {
    const { result } = renderHook(() => useGameProfile(""), {
      wrapper: createWrapper(),
    });

    expect(result.current.fetchStatus).toBe("idle");
    expect(getGameProfile).not.toHaveBeenCalled();
  });
});

describe("useCreateGameProfile", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("calls createGameProfile with projectId and data", async () => {
    vi.mocked(createGameProfile).mockResolvedValue(mockProfile);

    const { result } = renderHook(() => useCreateGameProfile("proj-1"), {
      wrapper: createWrapper(),
    });

    result.current.mutate({ genre: "puzzle", target_audience: "casual gamers" });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(createGameProfile).toHaveBeenCalledWith("proj-1", {
      genre: "puzzle",
      target_audience: "casual gamers",
    });
  });
});

describe("useUpdateGameProfile", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("calls updateGameProfile with projectId and data", async () => {
    vi.mocked(updateGameProfile).mockResolvedValue({
      ...mockProfile,
      genre: "strategy",
    });

    const { result } = renderHook(() => useUpdateGameProfile("proj-1"), {
      wrapper: createWrapper(),
    });

    result.current.mutate({ genre: "strategy" });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(updateGameProfile).toHaveBeenCalledWith("proj-1", {
      genre: "strategy",
    });
  });
});
