"use client";

import { Play } from "lucide-react";

interface VideoPreviewProps {
  url: string | null;
}

export function VideoPreview({ url }: VideoPreviewProps) {
  if (!url) {
    return (
      <div className="flex aspect-video max-w-2xl items-center justify-center rounded-lg bg-muted">
        <div className="flex flex-col items-center gap-2 text-muted-foreground">
          <Play className="h-8 w-8" />
          <p className="text-sm">No video yet</p>
        </div>
      </div>
    );
  }

  return (
    <video
      src={url}
      controls
      className="aspect-video max-w-2xl rounded-lg bg-black"
    >
      Your browser does not support the video tag.
    </video>
  );
}
