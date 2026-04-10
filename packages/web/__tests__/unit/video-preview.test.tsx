import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { VideoPreview } from "@/components/video-preview";

describe("VideoPreview", () => {
  it("renders placeholder when no URL", () => {
    render(<VideoPreview url={null} />);
    expect(screen.getByText("No video yet")).toBeInTheDocument();
  });

  it("renders video element when URL is provided", () => {
    render(<VideoPreview url="https://s3.example.com/video.mp4" />);
    const video = document.querySelector("video");
    expect(video).toBeInTheDocument();
    expect(video).toHaveAttribute("src", "https://s3.example.com/video.mp4");
    expect(video).toHaveAttribute("controls");
  });
});
