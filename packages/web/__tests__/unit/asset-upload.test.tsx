import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { AssetUpload } from "@/components/asset-upload";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

vi.mock("@/lib/hooks/use-assets", () => ({
  useAssets: vi.fn(() => ({ data: [], isLoading: false, isError: false })),
  useUploadAsset: vi.fn(() => ({ mutate: vi.fn(), isPending: false })),
  useDeleteAsset: vi.fn(() => ({ mutate: vi.fn(), isPending: false })),
}));

function renderWithProviders(ui: React.ReactElement) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return render(
    <QueryClientProvider client={queryClient}>{ui}</QueryClientProvider>,
  );
}

describe("AssetUpload", () => {
  it("renders Assets card title", () => {
    renderWithProviders(<AssetUpload projectId="proj-1" />);
    expect(screen.getByText("Assets")).toBeInTheDocument();
  });

  it("renders the drop zone", () => {
    renderWithProviders(<AssetUpload projectId="proj-1" />);
    expect(screen.getByText(/drag files here/i)).toBeInTheDocument();
  });

  it("renders the asset list empty state", () => {
    renderWithProviders(<AssetUpload projectId="proj-1" />);
    expect(screen.getByText(/no assets uploaded yet/i)).toBeInTheDocument();
  });
});
