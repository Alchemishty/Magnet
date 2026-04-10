// @vitest-environment jsdom
import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { AssetList } from "@/components/asset-list";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

// Mock the hooks
vi.mock("@/lib/hooks/use-assets", () => ({
  useAssets: vi.fn(),
  useDeleteAsset: vi.fn(() => ({ mutate: vi.fn(), isPending: false })),
}));

import { useAssets } from "@/lib/hooks/use-assets";

const mockAsset = {
  id: "asset-1",
  project_id: "proj-1",
  asset_type: "gameplay",
  s3_key: "uploads/proj-1/abc_video.mp4",
  filename: "gameplay-recording.mp4",
  content_type: "video/mp4",
  size_bytes: 1048576,
  duration_ms: null,
  width: null,
  height: null,
  metadata_: {},
  created_at: "2026-03-11T00:00:00Z",
  updated_at: null,
};

function renderWithProviders(ui: React.ReactElement) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return render(
    <QueryClientProvider client={queryClient}>{ui}</QueryClientProvider>,
  );
}

describe("AssetList", () => {
  it('shows "No assets uploaded yet." when assets array is empty', () => {
    vi.mocked(useAssets).mockReturnValue({
      data: [],
      isLoading: false,
      isError: false,
    } as any);

    renderWithProviders(<AssetList projectId="proj-1" />);
    expect(screen.getByText("No assets uploaded yet.")).toBeInTheDocument();
  });

  it("shows loading message when loading", () => {
    vi.mocked(useAssets).mockReturnValue({
      data: undefined,
      isLoading: true,
      isError: false,
    } as any);

    renderWithProviders(<AssetList projectId="proj-1" />);
    expect(screen.getByText("Loading assets...")).toBeInTheDocument();
  });

  it("shows error message when query fails", () => {
    vi.mocked(useAssets).mockReturnValue({
      data: undefined,
      isLoading: false,
      isError: true,
    } as any);

    renderWithProviders(<AssetList projectId="proj-1" />);
    expect(screen.getByText("Failed to load assets.")).toBeInTheDocument();
  });

  it("renders asset filenames when assets exist", () => {
    vi.mocked(useAssets).mockReturnValue({
      data: [mockAsset],
      isLoading: false,
      isError: false,
    } as any);

    renderWithProviders(<AssetList projectId="proj-1" />);
    expect(screen.getByText("gameplay-recording.mp4")).toBeInTheDocument();
  });

  it("renders asset type badges", () => {
    vi.mocked(useAssets).mockReturnValue({
      data: [mockAsset],
      isLoading: false,
      isError: false,
    } as any);

    renderWithProviders(<AssetList projectId="proj-1" />);
    expect(screen.getByText("gameplay")).toBeInTheDocument();
  });

  it("renders delete buttons for each asset", () => {
    vi.mocked(useAssets).mockReturnValue({
      data: [mockAsset],
      isLoading: false,
      isError: false,
    } as any);

    renderWithProviders(<AssetList projectId="proj-1" />);
    const deleteButton = screen.getByRole("button");
    expect(deleteButton).toBeInTheDocument();
  });

  it("renders formatted file size", () => {
    vi.mocked(useAssets).mockReturnValue({
      data: [mockAsset],
      isLoading: false,
      isError: false,
    } as any);

    renderWithProviders(<AssetList projectId="proj-1" />);
    expect(screen.getByText("1.0 MB")).toBeInTheDocument();
  });
});
