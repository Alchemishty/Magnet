import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { CreateProjectForm } from "@/components/create-project-form";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn() }),
}));

vi.mock("@/lib/api/projects", () => ({
  createProject: vi.fn(),
  listProjects: vi.fn(),
  getProject: vi.fn(),
  updateProject: vi.fn(),
  deleteProject: vi.fn(),
}));

function renderWithProviders(ui: React.ReactElement) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return render(
    <QueryClientProvider client={queryClient}>{ui}</QueryClientProvider>
  );
}

describe("CreateProjectForm", () => {
  it("renders project name input and submit button", () => {
    renderWithProviders(<CreateProjectForm />);
    expect(screen.getByLabelText(/project name/i)).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /create project/i })
    ).toBeInTheDocument();
  });

  it("disables submit button when name is empty", () => {
    renderWithProviders(<CreateProjectForm />);
    expect(
      screen.getByRole("button", { name: /create project/i })
    ).toBeDisabled();
  });

  it("enables submit button when name is entered", async () => {
    const user = userEvent.setup();
    renderWithProviders(<CreateProjectForm />);
    await user.type(screen.getByLabelText(/project name/i), "My Game");
    expect(
      screen.getByRole("button", { name: /create project/i })
    ).toBeEnabled();
  });
});
