import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import type {
  Asset,
  AssetCreate,
  PresignedUploadRequest,
  PresignedUploadResponse,
} from "@/lib/types/asset";

// Mock the client module before importing assets
vi.mock("@/lib/api/client", () => ({
  apiGet: vi.fn(),
  apiPost: vi.fn(),
  apiDelete: vi.fn(),
}));

import { apiGet, apiPost, apiDelete } from "@/lib/api/client";
import {
  requestPresignedUpload,
  uploadFileToS3,
  createAsset,
  listAssets,
  deleteAsset,
  getDownloadUrl,
} from "@/lib/api/assets";

const mockAsset: Asset = {
  id: "asset-1",
  project_id: "proj-1",
  asset_type: "gameplay",
  s3_key: "projects/proj-1/assets/video.mp4",
  filename: "video.mp4",
  content_type: "video/mp4",
  size_bytes: 1024000,
  duration_ms: 30000,
  width: 1920,
  height: 1080,
  metadata_: {},
  created_at: "2026-04-10T00:00:00Z",
  updated_at: null,
};

const mockPresignedResponse: PresignedUploadResponse = {
  upload_url: "https://s3.amazonaws.com/bucket/key?signature=abc",
  s3_key: "projects/proj-1/assets/video.mp4",
};

beforeEach(() => {
  vi.clearAllMocks();
});

afterEach(() => {
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
});

describe("requestPresignedUpload", () => {
  it("calls apiPost with correct path and body", async () => {
    vi.mocked(apiPost).mockResolvedValue(mockPresignedResponse);

    const body: PresignedUploadRequest = {
      filename: "video.mp4",
      content_type: "video/mp4",
      asset_type: "gameplay",
    };
    const result = await requestPresignedUpload("proj-1", body);

    expect(apiPost).toHaveBeenCalledWith(
      "/api/projects/proj-1/assets/presigned-upload",
      body,
    );
    expect(result).toEqual(mockPresignedResponse);
  });
});

describe("createAsset", () => {
  it("calls apiPost with correct path and body", async () => {
    vi.mocked(apiPost).mockResolvedValue(mockAsset);

    const body: AssetCreate = {
      asset_type: "gameplay",
      s3_key: "projects/proj-1/assets/video.mp4",
      filename: "video.mp4",
      content_type: "video/mp4",
      size_bytes: 1024000,
    };
    const result = await createAsset("proj-1", body);

    expect(apiPost).toHaveBeenCalledWith("/api/projects/proj-1/assets", body);
    expect(result).toEqual(mockAsset);
  });
});

describe("listAssets", () => {
  it("calls apiGet with correct path when no filter", async () => {
    vi.mocked(apiGet).mockResolvedValue([mockAsset]);

    const result = await listAssets("proj-1");

    expect(apiGet).toHaveBeenCalledWith("/api/projects/proj-1/assets");
    expect(result).toEqual([mockAsset]);
  });

  it("calls apiGet with asset_type query param when provided", async () => {
    vi.mocked(apiGet).mockResolvedValue([mockAsset]);

    const result = await listAssets("proj-1", "gameplay");

    expect(apiGet).toHaveBeenCalledWith(
      "/api/projects/proj-1/assets?asset_type=gameplay",
    );
    expect(result).toEqual([mockAsset]);
  });
});

describe("deleteAsset", () => {
  it("calls apiDelete with correct path", async () => {
    vi.mocked(apiDelete).mockResolvedValue(undefined);

    await deleteAsset("asset-1");

    expect(apiDelete).toHaveBeenCalledWith("/api/assets/asset-1");
  });
});

describe("getDownloadUrl", () => {
  it("calls apiGet with correct path", async () => {
    const mockResponse = { download_url: "https://s3.amazonaws.com/download" };
    vi.mocked(apiGet).mockResolvedValue(mockResponse);

    const result = await getDownloadUrl("asset-1");

    expect(apiGet).toHaveBeenCalledWith("/api/assets/asset-1/download-url");
    expect(result).toEqual(mockResponse);
  });
});

describe("uploadFileToS3", () => {
  it("calls fetch with PUT method and file body", async () => {
    const mockFetch = vi.fn().mockResolvedValue({ ok: true });
    vi.stubGlobal("fetch", mockFetch);

    const file = new File(["video-content"], "video.mp4", {
      type: "video/mp4",
    });
    await uploadFileToS3("https://s3.amazonaws.com/upload", file);

    expect(mockFetch).toHaveBeenCalledWith(
      "https://s3.amazonaws.com/upload",
      expect.objectContaining({
        method: "PUT",
        body: file,
        headers: { "Content-Type": "video/mp4" },
      }),
    );
  });

  it("throws on non-ok response", async () => {
    const mockFetch = vi
      .fn()
      .mockResolvedValue({ ok: false, status: 403 });
    vi.stubGlobal("fetch", mockFetch);

    const file = new File(["video-content"], "video.mp4", {
      type: "video/mp4",
    });

    await expect(
      uploadFileToS3("https://s3.amazonaws.com/upload", file),
    ).rejects.toThrow("S3 upload failed: 403");
  });
});
