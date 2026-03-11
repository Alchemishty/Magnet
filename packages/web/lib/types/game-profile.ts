export interface GameProfile {
  id: string;
  project_id: string;
  genre: string | null;
  target_audience: string | null;
  core_mechanics: string[] | null;
  art_style: string | null;
  brand_guidelines: Record<string, unknown> | null;
  competitors: string[] | null;
  key_selling_points: string[] | null;
  created_at: string;
  updated_at: string | null;
}

export interface GameProfileCreate {
  genre?: string | null;
  target_audience?: string | null;
  core_mechanics?: string[] | null;
  art_style?: string | null;
  brand_guidelines?: Record<string, unknown> | null;
  competitors?: string[] | null;
  key_selling_points?: string[] | null;
}

export type GameProfileUpdate = GameProfileCreate;
