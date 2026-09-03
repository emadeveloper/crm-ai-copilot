import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { createLead, fetchLead, fetchLeads, type LeadInput } from "../../api/leads";

export const leadsKey = ["leads"] as const;
export const leadKey = (id: string) => ["lead", id] as const;

export const REFETCH_MS = 5000;
export const DETAIL_REFETCH_MS = 3000;

const TERMINAL = new Set(["synced", "failed"]);

/** Poll the open lead detail until the lead reaches a terminal state. */
export function detailRefetchInterval(status: string | undefined): number | false {
  return status !== undefined && TERMINAL.has(status) ? false : DETAIL_REFETCH_MS;
}

export function useLeads() {
  return useQuery({ queryKey: leadsKey, queryFn: fetchLeads, refetchInterval: REFETCH_MS });
}

export function useLead(id: string) {
  return useQuery({
    queryKey: leadKey(id),
    queryFn: () => fetchLead(id),
    enabled: id.length > 0,
    refetchInterval: (query) => detailRefetchInterval(query.state.data?.status),
  });
}

export function useCreateLead() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: LeadInput) => createLead(body),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: leadsKey }),
  });
}
