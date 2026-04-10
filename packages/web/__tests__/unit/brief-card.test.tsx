import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { BriefCard } from "@/components/brief-card";

const mockBrief = {
  id: "brief-1",
  project_id: "proj-1",
  hook_type: "Fail/Challenge",
  narrative_angle: "Player struggles with level 50",
  script: "Can you beat this impossible level? Most players give up here.",
  voiceover_text: "Think you can do better?",
  target_emotion: "frustration",
  cta_text: "Download now",
  reference_ads: [],
  target_format: "9:16",
  target_duration: 15,
  status: "draft" as const,
  generated_by: "agent",
  scene_plan: { scenes: [
    { strategy: "GENERATE", type: "hook", duration: 2 },
    { strategy: "COMPOSE", type: "real_gameplay", duration: 5 },
    { strategy: "RENDER", type: "endcard", duration: 2 },
  ] },
  created_at: "2026-04-10T00:00:00Z",
  updated_at: null,
};

describe("BriefCard", () => {
  it("renders hook type", () => {
    render(<BriefCard brief={mockBrief} onApprove={vi.fn()} onDelete={vi.fn()} />);
    expect(screen.getByText("Fail/Challenge")).toBeInTheDocument();
  });

  it("renders script text", () => {
    render(<BriefCard brief={mockBrief} onApprove={vi.fn()} onDelete={vi.fn()} />);
    expect(screen.getByText(/impossible level/)).toBeInTheDocument();
  });

  it("renders status badge", () => {
    render(<BriefCard brief={mockBrief} onApprove={vi.fn()} onDelete={vi.fn()} />);
    expect(screen.getByText("draft")).toBeInTheDocument();
  });

  it("renders approve button for draft briefs", () => {
    render(<BriefCard brief={mockBrief} onApprove={vi.fn()} onDelete={vi.fn()} />);
    expect(screen.getByRole("button", { name: /approve/i })).toBeInTheDocument();
  });

  it("does not render approve button for approved briefs", () => {
    const approved = { ...mockBrief, status: "approved" as const };
    render(<BriefCard brief={approved} onApprove={vi.fn()} onDelete={vi.fn()} />);
    expect(screen.queryByRole("button", { name: /approve/i })).not.toBeInTheDocument();
  });

  it("calls onApprove when approve is clicked", async () => {
    const onApprove = vi.fn();
    render(<BriefCard brief={mockBrief} onApprove={onApprove} onDelete={vi.fn()} />);
    await userEvent.click(screen.getByRole("button", { name: /approve/i }));
    expect(onApprove).toHaveBeenCalled();
  });

  it("renders scene plan summary", () => {
    render(<BriefCard brief={mockBrief} onApprove={vi.fn()} onDelete={vi.fn()} />);
    expect(screen.getByText(/3 scenes/)).toBeInTheDocument();
  });
});
