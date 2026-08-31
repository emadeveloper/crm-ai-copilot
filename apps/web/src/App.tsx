import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { Dashboard } from "./Dashboard";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { retry: 1, refetchOnWindowFocus: false, staleTime: 2000 },
  },
});

export function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <Dashboard />
    </QueryClientProvider>
  );
}
