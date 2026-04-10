export type AssetType = "gameplay" | "screenshot" | "logo" | "character" | "audio";

export interface Asset {
  id: string;
  project_id: string;
  asset_type: AssetType;
  s3_key: string;
  filename: string;
  content_type: string | null;
  size_bytes: number | null;
  duration_ms: number | null;
  width: number | null;
  height: number | null;
  metadata_: Record<string, unknown>;
  created_at: string;
  updated_at: string | null;
}

export interface AssetCreate {
  asset_type: AssetType;
  s3_key: string;
  filename: string;
  content_type?: string | null;
  size_bytes?: number | null;
  duration_ms?: number | null;
  width?: number | null;
  height?: number | null;
  metadata_?: Record<string, unknown> | null;
}

export interface PresignedUploadRequest {
  filename: string;
  content_type: string;
  asset_type: AssetType;
}

export interface PresignedUploadResponse {
  upload_url: string;
  s3_key: string;
}
