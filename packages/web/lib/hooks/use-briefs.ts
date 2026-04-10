import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { listBriefs, generateConcepts, updateBrief, deleteBrief } from "@/lib/api/briefs";
import type { BriefStatus, BriefUpdate } from "@/lib/types/brief";

export function useBriefs(projectId: string, status?: BriefStatus) {
  return useQuery({
    queryKey: ["briefs", "list", projectId, status],
    queryFn: () => listBriefs(projectId, status),
    enabled: !!projectId,
  });
}

export function useGenerateConcepts(projectId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => generateConcepts(projectId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["briefs"] });
    },
  });
}

export function useUpdateBrief(briefId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: BriefUpdate) => updateBrief(briefId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["briefs"] });
    },
  });
}

export function useDeleteBrief() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (briefId: string) => deleteBrief(briefId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["briefs"] });
    },
  });
}
