import type {
  Asset,
  AssetCreate,
  AssetType,
  PresignedUploadRequest,
  PresignedUploadResponse,
} from "@/lib/types/asset";
import { apiGet, apiPost, apiDelete } from "./client";

export async function requestPresignedUpload(
  projectId: string,
  data: PresignedUploadRequest,
): Promise<PresignedUploadResponse> {
  return apiPost<PresignedUploadResponse>(
    `/api/projects/${projectId}/assets/presigned-upload`,
    data,
  );
}

export async function uploadFileToS3(
  uploadUrl: string,
  file: File,
): Promise<void> {
  const res = await fetch(uploadUrl, {
    method: "PUT",
    body: file,
    headers: { "Content-Type": file.type },
  });
  if (!res.ok) {
    throw new Error(`S3 upload failed: ${res.status}`);
  }
}

export async function createAsset(
  projectId: string,
  data: AssetCreate,
): Promise<Asset> {
  return apiPost<Asset>(`/api/projects/${projectId}/assets`, data);
}

export async function listAssets(
  projectId: string,
  assetType?: AssetType,
): Promise<Asset[]> {
  const params = new URLSearchParams();
  if (assetType) params.set("asset_type", assetType);
  const query = params.toString();
  return apiGet<Asset[]>(
    `/api/projects/${projectId}/assets${query ? `?${query}` : ""}`,
  );
}

export async function deleteAsset(assetId: string): Promise<void> {
  return apiDelete(`/api/assets/${assetId}`);
}

export async function getDownloadUrl(
  assetId: string,
): Promise<{ download_url: string }> {
  return apiGet<{ download_url: string }>(
    `/api/assets/${assetId}/download-url`,
  );
}
