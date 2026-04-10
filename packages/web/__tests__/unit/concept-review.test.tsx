import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { ConceptReview } from "@/components/concept-review";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

vi.mock("@/lib/hooks/use-briefs", () => ({
  useBriefs: vi.fn(() => ({ data: [], isLoading: false, isError: false })),
  useGenerateConcepts: vi.fn(() => ({ mutate: vi.fn(), isPending: false })),
  useUpdateBrief: vi.fn(() => ({ mutate: vi.fn(), isPending: false })),
  useDeleteBrief: vi.fn(() => ({ mutate: vi.fn(), isPending: false })),
}));

function renderWithProviders(ui: React.ReactElement) {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(<QueryClientProvider client={queryClient}>{ui}</QueryClientProvider>);
}

describe("ConceptReview", () => {
  it("renders Creative Concepts title", () => {
    renderWithProviders(<ConceptReview projectId="proj-1" />);
    expect(screen.getByText("Creative Concepts")).toBeInTheDocument();
  });

  it("renders Generate Concepts button", () => {
    renderWithProviders(<ConceptReview projectId="proj-1" />);
    expect(screen.getByRole("button", { name: /generate concepts/i })).toBeInTheDocument();
  });

  it("shows empty state when no briefs", () => {
    renderWithProviders(<ConceptReview projectId="proj-1" />);
    expect(screen.getByText(/no concepts yet/i)).toBeInTheDocument();
  });

  it("renders status filter badges", () => {
    renderWithProviders(<ConceptReview projectId="proj-1" />);
    expect(screen.getByText("All")).toBeInTheDocument();
    expect(screen.getByText("Draft")).toBeInTheDocument();
    expect(screen.getByText("Approved")).toBeInTheDocument();
  });
});
