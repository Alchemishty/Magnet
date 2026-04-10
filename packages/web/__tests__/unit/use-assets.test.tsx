import { renderHook, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { vi, describe, it, expect, beforeEach } from "vitest";
import type { ReactNode } from "react";

import {
  useAssets,
  useUploadAsset,
  useDeleteAsset,
} from "@/lib/hooks/use-assets";
import {
  listAssets,
  requestPresignedUpload,
  uploadFileToS3,
  createAsset,
  deleteAsset,
} from "@/lib/api/assets";
import type { Asset } from "@/lib/types/asset";

vi.mock("@/lib/api/assets", () => ({
  listAssets: vi.fn(),
  requestPresignedUpload: vi.fn(),
  uploadFileToS3: vi.fn(),
  createAsset: vi.fn(),
  deleteAsset: vi.fn(),
}));

const mockAsset: Asset = {
  id: "asset-1",
  project_id: "proj-1",
  asset_type: "gameplay",
  s3_key: "projects/proj-1/gameplay/clip.mp4",
  filename: "clip.mp4",
  content_type: "video/mp4",
  size_bytes: 1024,
  duration_ms: null,
  width: null,
  height: null,
  metadata_: {},
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

describe("useAssets", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("fetches assets for a given project", async () => {
    vi.mocked(listAssets).mockResolvedValue([mockAsset]);

    const { result } = renderHook(() => useAssets("proj-1"), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(listAssets).toHaveBeenCalledWith("proj-1", undefined);
    expect(result.current.data).toEqual([mockAsset]);
  });

  it("passes assetType filter to listAssets", async () => {
    vi.mocked(listAssets).mockResolvedValue([mockAsset]);

    const { result } = renderHook(() => useAssets("proj-1", "gameplay"), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(listAssets).toHaveBeenCalledWith("proj-1", "gameplay");
  });

  it("does not fetch when projectId is empty", () => {
    const { result } = renderHook(() => useAssets(""), {
      wrapper: createWrapper(),
    });

    expect(result.current.fetchStatus).toBe("idle");
    expect(listAssets).not.toHaveBeenCalled();
  });
});

describe("useDeleteAsset", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("calls deleteAsset with correct id", async () => {
    vi.mocked(deleteAsset).mockResolvedValue(undefined);

    const { result } = renderHook(() => useDeleteAsset(), {
      wrapper: createWrapper(),
    });

    result.current.mutate("asset-1");

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(deleteAsset).toHaveBeenCalledWith("asset-1");
  });
});

describe("useUploadAsset", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("chains presigned upload, S3 upload, and asset creation", async () => {
    vi.mocked(requestPresignedUpload).mockResolvedValue({
      upload_url: "https://s3.example.com/upload",
      s3_key: "projects/proj-1/gameplay/clip.mp4",
    });
    vi.mocked(uploadFileToS3).mockResolvedValue(undefined);
    vi.mocked(createAsset).mockResolvedValue(mockAsset);

    const file = new File(["video-data"], "clip.mp4", { type: "video/mp4" });

    const { result } = renderHook(() => useUploadAsset("proj-1"), {
      wrapper: createWrapper(),
    });

    result.current.mutate({ file, assetType: "gameplay" });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(requestPresignedUpload).toHaveBeenCalledWith("proj-1", {
      filename: "clip.mp4",
      content_type: "video/mp4",
      asset_type: "gameplay",
    });
    expect(uploadFileToS3).toHaveBeenCalledWith(
      "https://s3.example.com/upload",
      file,
    );
    expect(createAsset).toHaveBeenCalledWith("proj-1", {
      asset_type: "gameplay",
      s3_key: "projects/proj-1/gameplay/clip.mp4",
      filename: "clip.mp4",
      content_type: "video/mp4",
      size_bytes: 10,
    });
    expect(result.current.data).toEqual(mockAsset);
  });
});
