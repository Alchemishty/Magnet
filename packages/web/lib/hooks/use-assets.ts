import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  listAssets,
  requestPresignedUpload,
  uploadFileToS3,
  createAsset,
  deleteAsset,
} from "@/lib/api/assets";
import type { AssetType } from "@/lib/types/asset";

export function useAssets(projectId: string, assetType?: AssetType) {
  return useQuery({
    queryKey: ["assets", "list", projectId, assetType],
    queryFn: () => listAssets(projectId, assetType),
    enabled: !!projectId,
  });
}

export function useUploadAsset(projectId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({
      file,
      assetType,
    }: {
      file: File;
      assetType: AssetType;
    }) => {
      const { upload_url, s3_key } = await requestPresignedUpload(projectId, {
        filename: file.name,
        content_type: file.type,
        asset_type: assetType,
      });
      await uploadFileToS3(upload_url, file);
      return createAsset(projectId, {
        asset_type: assetType,
        s3_key,
        filename: file.name,
        content_type: file.type,
        size_bytes: file.size,
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["assets"] });
    },
  });
}

export function useDeleteAsset() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (assetId: string) => deleteAsset(assetId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["assets"] });
    },
  });
}
