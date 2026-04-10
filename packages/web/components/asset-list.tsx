"use client";

import { Video, Image, Palette, User, Music, Trash2 } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { useAssets, useDeleteAsset } from "@/lib/hooks/use-assets";
import type { AssetType } from "@/lib/types/asset";

const ASSET_ICONS: Record<AssetType, React.ElementType> = {
  gameplay: Video,
  screenshot: Image,
  logo: Palette,
  character: User,
  audio: Music,
};

function formatBytes(bytes: number | null): string {
  if (!bytes) return "\u2014";
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

interface AssetListProps {
  projectId: string;
}

export function AssetList({ projectId }: AssetListProps) {
  const { data: assets, isLoading, isError } = useAssets(projectId);
  const deleteAsset = useDeleteAsset();

  if (isLoading) {
    return <p className="text-sm text-muted-foreground">Loading assets...</p>;
  }

  if (isError) {
    return <p className="text-sm text-destructive">Failed to load assets.</p>;
  }

  if (!assets || assets.length === 0) {
    return (
      <p className="text-sm text-muted-foreground">No assets uploaded yet.</p>
    );
  }

  return (
    <div className="space-y-2">
      {assets.map((asset) => {
        const Icon = ASSET_ICONS[asset.asset_type as AssetType] || Image;
        return (
          <div
            key={asset.id}
            className="flex items-center gap-3 rounded-md border p-3"
          >
            <Icon className="h-4 w-4 text-muted-foreground" />
            <span className="flex-1 truncate text-sm">{asset.filename}</span>
            <Badge variant="secondary">{asset.asset_type}</Badge>
            <span className="text-xs text-muted-foreground">
              {formatBytes(asset.size_bytes)}
            </span>
            <Button
              variant="ghost"
              size="icon"
              onClick={() => deleteAsset.mutate(asset.id)}
              disabled={deleteAsset.isPending}
            >
              <Trash2 className="h-4 w-4" />
            </Button>
          </div>
        );
      })}
    </div>
  );
}
