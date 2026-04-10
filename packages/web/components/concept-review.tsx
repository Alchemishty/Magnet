"use client";

import { useState } from "react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Sparkles } from "lucide-react";
import { BriefCard } from "@/components/brief-card";
import { useBriefs, useGenerateConcepts, useUpdateBrief, useDeleteBrief } from "@/lib/hooks/use-briefs";
import type { Brief, BriefStatus } from "@/lib/types/brief";

const STATUS_FILTERS: { label: string; value: BriefStatus | undefined }[] = [
  { label: "All", value: undefined },
  { label: "Draft", value: "draft" },
  { label: "Approved", value: "approved" },
];

interface ConceptReviewProps {
  projectId: string;
}

export function ConceptReview({ projectId }: ConceptReviewProps) {
  const [statusFilter, setStatusFilter] = useState<BriefStatus | undefined>(undefined);
  const { data: briefs, isLoading, isError } = useBriefs(projectId, statusFilter);
  const generateConcepts = useGenerateConcepts(projectId);
  const deleteBrief = useDeleteBrief();

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle>Creative Concepts</CardTitle>
          <Button
            onClick={() => generateConcepts.mutate()}
            disabled={generateConcepts.isPending}
          >
            <Sparkles className="mr-2 h-4 w-4" />
            {generateConcepts.isPending ? "Generating..." : "Generate Concepts"}
          </Button>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Status filter buttons */}
        <div className="flex gap-2">
          {STATUS_FILTERS.map((filter) => (
            <Badge
              key={filter.label}
              variant={statusFilter === filter.value ? "default" : "secondary"}
              className="cursor-pointer"
              onClick={() => setStatusFilter(filter.value)}
            >
              {filter.label}
            </Badge>
          ))}
        </div>

        {/* Content */}
        {isLoading && (
          <p className="text-sm text-muted-foreground">Loading concepts...</p>
        )}

        {isError && (
          <p className="text-sm text-destructive">Failed to load concepts.</p>
        )}

        {!isLoading && !isError && briefs && briefs.length === 0 && (
          <p className="text-sm text-muted-foreground">
            No concepts yet. Generate concepts from your game profile.
          </p>
        )}

        {briefs && briefs.length > 0 && (
          <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
            {briefs.map((brief) => (
              <BriefCardWrapper
                key={brief.id}
                brief={brief}
                onDelete={() => deleteBrief.mutate(brief.id)}
              />
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

// Wrapper to scope useUpdateBrief to each brief
function BriefCardWrapper({ brief, onDelete }: { brief: Brief; onDelete: () => void }) {
  const updateBrief = useUpdateBrief(brief.id);
  return (
    <BriefCard
      brief={brief}
      onApprove={() => updateBrief.mutate({ status: "approved" })}
      onDelete={onDelete}
    />
  );
}
