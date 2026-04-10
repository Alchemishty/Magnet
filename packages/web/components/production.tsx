"use client";

import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Clapperboard } from "lucide-react";
import { JobCard } from "@/components/job-card";
import { VideoPreview } from "@/components/video-preview";
import { useBriefs } from "@/lib/hooks/use-briefs";
import { useJobs, useCreateJob } from "@/lib/hooks/use-jobs";
import { useBriefProgress } from "@/lib/useBriefProgress";
import type { Brief } from "@/lib/types/brief";

interface ProductionProps {
  projectId: string;
}

export function Production({ projectId }: ProductionProps) {
  const { data: briefs, isLoading, isError } = useBriefs(projectId, "approved");

  return (
    <Card>
      <CardHeader>
        <CardTitle>Production</CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        {isLoading && (
          <p className="text-sm text-muted-foreground">Loading approved briefs...</p>
        )}
        {isError && (
          <p className="text-sm text-destructive">Failed to load briefs.</p>
        )}
        {!isLoading && !isError && briefs && briefs.length === 0 && (
          <p className="text-sm text-muted-foreground">
            No approved briefs. Approve briefs in the Concept Review section above.
          </p>
        )}
        {briefs && briefs.length > 0 && (
          <div className="space-y-6">
            {briefs.map((brief) => (
              <BriefProduction key={brief.id} brief={brief} />
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

function BriefProduction({ brief }: { brief: Brief }) {
  const { data: jobs } = useJobs(brief.id);
  const createJob = useCreateJob(brief.id);
  const { events } = useBriefProgress(brief.id);

  const hasActiveJob = jobs?.some(
    (j) => j.status === "queued" || j.status === "rendering",
  );
  const doneJob = jobs?.find((j) => j.status === "done");

  return (
    <div className="space-y-3 rounded-lg border p-4">
      <div className="flex items-center justify-between">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            {brief.hook_type && <Badge variant="outline">{brief.hook_type}</Badge>}
            <span className="text-sm text-muted-foreground">
              {brief.target_format} &middot; {brief.target_duration}s
            </span>
          </div>
          {brief.narrative_angle && (
            <p className="text-sm">{brief.narrative_angle}</p>
          )}
        </div>
        <Button
          onClick={() => createJob.mutate(undefined)}
          disabled={createJob.isPending || !!hasActiveJob}
        >
          <Clapperboard className="mr-2 h-4 w-4" />
          {createJob.isPending ? "Starting..." : "Produce Video"}
        </Button>
      </div>

      {jobs && jobs.length > 0 && (
        <div className="space-y-2">
          {jobs.map((job) => (
            <JobCard
              key={job.id}
              job={job}
              progress={events.get(job.id) ?? undefined}
            />
          ))}
        </div>
      )}

      {doneJob && <VideoPreview url={null} />}
    </div>
  );
}
