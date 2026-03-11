// @vitest-environment jsdom
import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { Sidebar } from "@/components/sidebar";

// Mock next/link since we're outside Next.js
vi.mock("next/link", () => ({
  default: ({ children, href, ...props }: any) => (
    <a href={href} {...props}>
      {children}
    </a>
  ),
}));

describe("Sidebar", () => {
  it("renders Magnet branding", () => {
    render(<Sidebar />);
    expect(screen.getByText("Magnet")).toBeInTheDocument();
  });

  it("renders Projects nav link pointing to /projects", () => {
    render(<Sidebar />);
    const link = screen.getByRole("link", { name: /projects/i });
    expect(link).toHaveAttribute("href", "/projects");
  });

  it("renders Creative Library as disabled", () => {
    render(<Sidebar />);
    expect(screen.getByText(/creative library/i)).toBeInTheDocument();
    // Should NOT be a link
    expect(
      screen.queryByRole("link", { name: /creative library/i })
    ).not.toBeInTheDocument();
  });

  it("renders Settings as disabled", () => {
    render(<Sidebar />);
    expect(screen.getByText(/settings/i)).toBeInTheDocument();
    expect(
      screen.queryByRole("link", { name: /settings/i })
    ).not.toBeInTheDocument();
  });

  it("renders user avatar area", () => {
    render(<Sidebar />);
    expect(screen.getByText("U")).toBeInTheDocument();
  });
});
