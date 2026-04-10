import { Card, CardHeader, CardContent, CardFooter } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Trash2, Check } from "lucide-react";
import type { Brief } from "@/lib/types/brief";

interface BriefCardProps {
  brief: Brief;
  onApprove: () => void;
  onDelete: () => void;
}

interface Scene {
  strategy: string;
  [key: string]: unknown;
}

function getStrategyBreakdown(scenes: Scene[]): string {
  const counts: Record<string, number> = {};
  for (const scene of scenes) {
    counts[scene.strategy] = (counts[scene.strategy] || 0) + 1;
  }
  return Object.entries(counts)
    .map(([strategy, count]) => `${count} ${strategy}`)
    .join(", ");
}

function getScenePlanSummary(scenePlan: Record<string, unknown> | null): string | null {
  if (!scenePlan) return null;
  const scenes = scenePlan.scenes as Scene[] | undefined;
  if (!Array.isArray(scenes) || scenes.length === 0) return null;
  const breakdown = getStrategyBreakdown(scenes);
  return `${scenes.length} scenes: ${breakdown}`;
}

export function BriefCard({ brief, onApprove, onDelete }: BriefCardProps) {
  const isApproved = brief.status === "approved";
  const borderClass = isApproved ? "border-primary" : "";
  const sceneSummary = getScenePlanSummary(brief.scene_plan);

  return (
    <Card className={borderClass}>
      <CardHeader>
        <div className="flex items-center gap-2 flex-wrap">
          {brief.hook_type && <Badge variant="outline">{brief.hook_type}</Badge>}
          <Badge variant={brief.status === "draft" ? "secondary" : "default"}>
            {brief.status}
          </Badge>
          <span className="ml-auto text-xs text-muted-foreground">
            {brief.generated_by === "agent" ? "AI" : "Human"}
          </span>
        </div>
      </CardHeader>

      <CardContent className="space-y-3">
        {brief.narrative_angle && (
          <div>
            <span className="text-sm font-bold">Narrative angle: </span>
            <span className="text-sm">{brief.narrative_angle}</span>
          </div>
        )}

        {brief.script && (
          <p className="text-sm text-muted-foreground line-clamp-3">
            {brief.script}
          </p>
        )}

        {brief.target_emotion && (
          <div>
            <span className="text-sm font-bold">Emotion: </span>
            <span className="text-sm">{brief.target_emotion}</span>
          </div>
        )}

        {brief.cta_text && (
          <div>
            <span className="text-sm font-bold">CTA: </span>
            <span className="text-sm">{brief.cta_text}</span>
          </div>
        )}

        {sceneSummary && (
          <p className="text-sm text-muted-foreground">{sceneSummary}</p>
        )}
      </CardContent>

      <CardFooter className="justify-between">
        <span className="text-xs text-muted-foreground">
          {brief.target_format} &middot; {brief.target_duration}s
        </span>
        <div className="flex gap-2">
          {brief.status === "draft" && (
            <Button size="sm" onClick={onApprove}>
              <Check className="mr-1 h-4 w-4" />
              Approve
            </Button>
          )}
          <Button size="sm" variant="ghost" onClick={onDelete} className="text-destructive">
            <Trash2 className="mr-1 h-4 w-4" />
            Delete
          </Button>
        </div>
      </CardFooter>
    </Card>
  );
}
