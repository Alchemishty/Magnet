import type {
  GameProfile,
  GameProfileCreate,
  GameProfileUpdate,
} from "@/lib/types/game-profile";
import { apiGet, apiPost, apiPatch } from "./client";

export async function createGameProfile(
  projectId: string,
  data: GameProfileCreate,
): Promise<GameProfile> {
  return apiPost<GameProfile>(
    `/api/projects/${projectId}/game-profile`,
    data,
  );
}

export async function getGameProfile(projectId: string): Promise<GameProfile> {
  return apiGet<GameProfile>(`/api/projects/${projectId}/game-profile`);
}

export async function updateGameProfile(
  projectId: string,
  data: GameProfileUpdate,
): Promise<GameProfile> {
  return apiPatch<GameProfile>(
    `/api/projects/${projectId}/game-profile`,
    data,
  );
}
