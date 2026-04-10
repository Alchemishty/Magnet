import { Badge } from "@/components/ui/badge";
import type { Job, JobStatus } from "@/lib/types/job";
import type { ProgressEvent } from "@/lib/types/progress";

interface JobCardProps {
  job: Job;
  progress?: ProgressEvent;
}

const statusBadgeVariant: Record<JobStatus, "secondary" | "default" | "outline" | "destructive"> = {
  queued: "secondary",
  rendering: "default",
  done: "outline",
  failed: "destructive",
};

function formatDuration(ms: number): string {
  return `${(ms / 1000).toFixed(1)}s`;
}

function formatTime(iso: string): string {
  return new Date(iso).toLocaleTimeString();
}

export function JobCard({ job, progress }: JobCardProps) {
  const variant = statusBadgeVariant[job.status];

  return (
    <div className="flex items-center gap-4 rounded-lg border p-3">
      <Badge
        variant={variant}
        className={job.status === "done" ? "border-green-500 text-green-600" : undefined}
      >
        {job.status}
      </Badge>

      <div className="flex-1 min-w-0">
        {job.status === "queued" && (
          <p className="text-sm text-muted-foreground">Waiting in queue...</p>
        )}

        {job.status === "rendering" && (
          <div className="space-y-1">
            {progress ? (
              <p className="text-sm">
                {progress.phase} &middot; {progress.progress_pct}%
              </p>
            ) : (
              <p className="text-sm text-muted-foreground">Rendering...</p>
            )}
            <div className="h-2 rounded-full bg-muted">
              <div
                className="h-2 rounded-full bg-primary transition-all"
                style={{ width: `${progress?.progress_pct ?? 0}%` }}
              />
            </div>
          </div>
        )}

        {job.status === "done" && (
          <div className="flex items-center gap-2">
            <span className="text-sm font-medium text-green-600">Complete</span>
            {job.render_duration_ms != null && (
              <span className="text-sm text-muted-foreground">
                {formatDuration(job.render_duration_ms)}
              </span>
            )}
          </div>
        )}

        {job.status === "failed" && job.error_message && (
          <p className="text-sm text-destructive truncate">{job.error_message}</p>
        )}
      </div>

      <span className="text-xs text-muted-foreground whitespace-nowrap">
        {formatTime(job.created_at)}
      </span>
    </div>
  );
}
