import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { createJob, listJobs, getJob } from "@/lib/api/jobs";
import type { JobCreate } from "@/lib/types/job";

export function useJobs(briefId: string) {
  return useQuery({
    queryKey: ["jobs", "list", briefId],
    queryFn: () => listJobs(briefId),
    enabled: !!briefId,
  });
}

export function useJob(jobId: string) {
  return useQuery({
    queryKey: ["jobs", "detail", jobId],
    queryFn: () => getJob(jobId),
    enabled: !!jobId,
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      if (status === "queued" || status === "rendering") return 5000;
      return false;
    },
  });
}

export function useCreateJob(briefId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data?: JobCreate) => createJob(briefId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["jobs"] });
      queryClient.invalidateQueries({ queryKey: ["briefs"] });
    },
  });
}
