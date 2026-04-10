import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { DropZone } from "@/components/drop-zone";

describe("DropZone", () => {
  it("renders drop area text", () => {
    render(<DropZone onFiles={vi.fn()} />);
    expect(screen.getByText(/drag files here/i)).toBeInTheDocument();
  });

  it("renders upload icon", () => {
    render(<DropZone onFiles={vi.fn()} />);
    // lucide icons render as svg
    expect(document.querySelector("svg")).toBeInTheDocument();
  });

  it("calls onFiles when files are selected via input", () => {
    const onFiles = vi.fn();
    render(<DropZone onFiles={onFiles} />);
    const input = screen.getByTestId("file-input");
    const file = new File(["content"], "test.png", { type: "image/png" });
    fireEvent.change(input, { target: { files: [file] } });
    expect(onFiles).toHaveBeenCalledWith([file]);
  });

  it("does not call onFiles when disabled", () => {
    const onFiles = vi.fn();
    render(<DropZone onFiles={onFiles} disabled />);
    const input = screen.getByTestId("file-input");
    const file = new File(["content"], "test.png", { type: "image/png" });
    fireEvent.change(input, { target: { files: [file] } });
    expect(onFiles).not.toHaveBeenCalled();
  });
});
