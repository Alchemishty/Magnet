import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { Production } from "@/components/production";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

vi.mock("@/lib/hooks/use-briefs", () => ({
  useBriefs: vi.fn(() => ({ data: [], isLoading: false, isError: false })),
}));

vi.mock("@/lib/hooks/use-jobs", () => ({
  useJobs: vi.fn(() => ({ data: [] })),
  useCreateJob: vi.fn(() => ({ mutate: vi.fn(), isPending: false })),
}));

vi.mock("@/lib/useBriefProgress", () => ({
  useBriefProgress: vi.fn(() => ({ events: new Map(), isConnected: false })),
}));

function renderWithProviders(ui: React.ReactElement) {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(<QueryClientProvider client={queryClient}>{ui}</QueryClientProvider>);
}

describe("Production", () => {
  it("renders Production title", () => {
    renderWithProviders(<Production projectId="proj-1" />);
    expect(screen.getByText("Production")).toBeInTheDocument();
  });

  it("shows empty state when no approved briefs", () => {
    renderWithProviders(<Production projectId="proj-1" />);
    expect(screen.getByText(/no approved briefs/i)).toBeInTheDocument();
  });
});
