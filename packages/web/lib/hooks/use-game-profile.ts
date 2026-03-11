import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";

import {
  getGameProfile,
  createGameProfile,
  updateGameProfile,
} from "@/lib/api/game-profiles";
import type {
  GameProfileCreate,
  GameProfileUpdate,
} from "@/lib/types/game-profile";

export function useGameProfile(projectId: string) {
  return useQuery({
    queryKey: ["game-profile", projectId],
    queryFn: () => getGameProfile(projectId),
    enabled: !!projectId,
  });
}

export function useCreateGameProfile(projectId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: GameProfileCreate) =>
      createGameProfile(projectId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ["game-profile", projectId],
      });
    },
  });
}

export function useUpdateGameProfile(projectId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: GameProfileUpdate) =>
      updateGameProfile(projectId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ["game-profile", projectId],
      });
    },
  });
}
