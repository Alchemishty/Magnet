// @vitest-environment jsdom
import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { ProjectCard } from "@/components/project-card";

vi.mock("next/link", () => ({
  default: ({ children, href, ...props }: any) => (
    <a href={href} {...props}>
      {children}
    </a>
  ),
}));

const mockProject = {
  id: "proj-1",
  user_id: "user-1",
  name: "Test Game",
  status: "active",
  created_at: "2026-03-01T00:00:00Z",
  updated_at: null,
};

describe("ProjectCard", () => {
  it("renders project name", () => {
    render(<ProjectCard project={mockProject} />);
    expect(screen.getByText("Test Game")).toBeInTheDocument();
  });

  it("renders status badge", () => {
    render(<ProjectCard project={mockProject} />);
    expect(screen.getByText("active")).toBeInTheDocument();
  });

  it("renders formatted date", () => {
    render(<ProjectCard project={mockProject} />);
    // toLocaleDateString output varies by locale, just check "Created" prefix exists
    expect(screen.getByText(/Created/)).toBeInTheDocument();
  });

  it("links to project detail page", () => {
    render(<ProjectCard project={mockProject} />);
    const link = screen.getByRole("link");
    expect(link).toHaveAttribute("href", "/projects/proj-1");
  });
});
