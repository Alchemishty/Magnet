export type BriefStatus = "draft" | "approved" | "producing" | "complete";

export interface Brief {
  id: string;
  project_id: string;
  hook_type: string | null;
  narrative_angle: string | null;
  script: string | null;
  voiceover_text: string | null;
  target_emotion: string | null;
  cta_text: string | null;
  reference_ads: string[];
  target_format: string;
  target_duration: number;
  status: BriefStatus;
  generated_by: string;
  scene_plan: Record<string, unknown> | null;
  created_at: string;
  updated_at: string | null;
}

export interface BriefUpdate {
  hook_type?: string | null;
  narrative_angle?: string | null;
  script?: string | null;
  voiceover_text?: string | null;
  target_emotion?: string | null;
  cta_text?: string | null;
  status?: BriefStatus;
  scene_plan?: Record<string, unknown> | null;
  target_format?: string;
  target_duration?: number;
}
