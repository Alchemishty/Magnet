"use client";

import { useState } from "react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { DropZone } from "@/components/drop-zone";
import { AssetList } from "@/components/asset-list";
import { useUploadAsset } from "@/lib/hooks/use-assets";
import type { AssetType } from "@/lib/types/asset";

function detectAssetType(file: File): AssetType {
  if (file.type.startsWith("video/")) return "gameplay";
  if (file.type.startsWith("image/")) return "screenshot";
  if (file.type.startsWith("audio/")) return "audio";
  return "screenshot";
}

interface UploadItem {
  id: string;
  filename: string;
  status: "uploading" | "done" | "error";
  error?: string;
}

interface AssetUploadProps {
  projectId: string;
}

export function AssetUpload({ projectId }: AssetUploadProps) {
  const [uploads, setUploads] = useState<UploadItem[]>([]);
  const uploadAsset = useUploadAsset(projectId);

  const handleFiles = (files: File[]) => {
    files.forEach((file) => {
      const id = `${Date.now()}-${file.name}`;
      const assetType = detectAssetType(file);

      setUploads((prev) => [
        ...prev,
        { id, filename: file.name, status: "uploading" },
      ]);

      uploadAsset.mutate(
        { file, assetType },
        {
          onSuccess: () => {
            setUploads((prev) =>
              prev.map((u) => (u.id === id ? { ...u, status: "done" } : u)),
            );
          },
          onError: (err) => {
            setUploads((prev) =>
              prev.map((u) =>
                u.id === id
                  ? {
                      ...u,
                      status: "error",
                      error:
                        err instanceof Error ? err.message : "Upload failed",
                    }
                  : u,
              ),
            );
          },
        },
      );
    });
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Assets</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <DropZone onFiles={handleFiles} disabled={uploadAsset.isPending} />

        {uploads.length > 0 && (
          <div className="space-y-1">
            {uploads.map((upload) => (
              <div key={upload.id} className="flex items-center gap-2 text-sm">
                <span className="truncate flex-1">{upload.filename}</span>
                {upload.status === "uploading" && (
                  <Badge variant="secondary">Uploading...</Badge>
                )}
                {upload.status === "done" && (
                  <Badge variant="default">Done</Badge>
                )}
                {upload.status === "error" && (
                  <Badge variant="destructive">
                    {upload.error || "Failed"}
                  </Badge>
                )}
              </div>
            ))}
          </div>
        )}

        <AssetList projectId={projectId} />
      </CardContent>
    </Card>
  );
}
