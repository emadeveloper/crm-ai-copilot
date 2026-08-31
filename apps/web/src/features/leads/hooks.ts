import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { createLead, fetchLead, fetchLeads, type LeadInput } from "../../api/leads";

export const leadsKey = ["leads"] as const;
export const leadKey = (id: string) => ["lead", id] as const;

export const REFETCH_MS = 5000;

export function useLeads() {
  return useQuery({ queryKey: leadsKey, queryFn: fetchLeads, refetchInterval: REFETCH_MS });
}

export function useLead(id: string) {
  return useQuery({
    queryKey: leadKey(id),
    queryFn: () => fetchLead(id),
    enabled: id.length > 0,
  });
}

export function useCreateLead() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: LeadInput) => createLead(body),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: leadsKey }),
  });
}
