import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { GameProfileForm } from "@/components/game-profile-form";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

vi.mock("@/lib/api/game-profiles", () => ({
  getGameProfile: vi.fn().mockResolvedValue(null),
  createGameProfile: vi.fn(),
  updateGameProfile: vi.fn(),
}));

function renderWithProviders(ui: React.ReactElement) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return render(
    <QueryClientProvider client={queryClient}>{ui}</QueryClientProvider>
  );
}

describe("GameProfileForm", () => {
  it("renders all form fields", async () => {
    renderWithProviders(<GameProfileForm projectId="proj-1" />);
    expect(await screen.findByLabelText(/genre/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/target audience/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/art style/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/brand guidelines/i)).toBeInTheDocument();
  });

  it("shows Create Profile button when no existing profile", async () => {
    renderWithProviders(<GameProfileForm projectId="proj-1" />);
    expect(
      await screen.findByRole("button", { name: /create profile/i })
    ).toBeInTheDocument();
  });
});
