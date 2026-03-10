// @vitest-environment jsdom
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { renderHook, act } from "@testing-library/react";
import { useBriefProgress } from "../../lib/useBriefProgress";

class MockWebSocket {
  static instances: MockWebSocket[] = [];
  url: string;
  onopen: (() => void) | null = null;
  onmessage: ((event: { data: string }) => void) | null = null;
  onclose: (() => void) | null = null;
  onerror: ((event: unknown) => void) | null = null;
  readyState = 0;
  closeCalled = false;

  constructor(url: string) {
    this.url = url;
    MockWebSocket.instances.push(this);
    setTimeout(() => {
      this.readyState = 1;
      this.onopen?.();
    }, 0);
  }

  close() {
    this.closeCalled = true;
    this.readyState = 3;
  }

  simulateMessage(data: string) {
    this.onmessage?.({ data });
  }

  simulateClose() {
    this.onclose?.();
  }
}

beforeEach(() => {
  MockWebSocket.instances = [];
  vi.stubGlobal("WebSocket", MockWebSocket);
  vi.stubGlobal(
    "process",
    { env: { NEXT_PUBLIC_API_WS_URL: "ws://localhost:8000" } },
  );
});

afterEach(() => {
  vi.restoreAllMocks();
});

describe("useBriefProgress", () => {
  it("returns empty events and disconnected when briefId is null", () => {
    const { result } = renderHook(() => useBriefProgress(null));
    expect(result.current.events.size).toBe(0);
    expect(result.current.isConnected).toBe(false);
    expect(MockWebSocket.instances).toHaveLength(0);
  });

  it("connects to correct WebSocket URL", () => {
    const briefId = "abc-123";
    renderHook(() => useBriefProgress(briefId));
    expect(MockWebSocket.instances).toHaveLength(1);
    expect(MockWebSocket.instances[0].url).toBe(
      `ws://localhost:8000/ws/briefs/${briefId}/progress`,
    );
  });

  it("updates events map on incoming messages", async () => {
    const briefId = "abc-123";
    const { result } = renderHook(() => useBriefProgress(briefId));

    await vi.waitFor(() => {
      expect(MockWebSocket.instances).toHaveLength(1);
    });

    const ws = MockWebSocket.instances[0];

    await act(async () => {
      ws.onopen?.();
    });

    const event = JSON.stringify({
      job_id: "job-1",
      brief_id: briefId,
      status: "rendering",
      phase: "PREPARE",
      progress_pct: 40,
      message: "Preparing",
      timestamp: "2026-03-11T00:00:00Z",
    });

    await act(async () => {
      ws.simulateMessage(event);
    });

    expect(result.current.events.size).toBe(1);
    expect(result.current.events.get("job-1")?.status).toBe("rendering");
    expect(result.current.events.get("job-1")?.progress_pct).toBe(40);
  });

  it("tracks multiple jobs in the events map", async () => {
    const briefId = "abc-123";
    const { result } = renderHook(() => useBriefProgress(briefId));

    await vi.waitFor(() => {
      expect(MockWebSocket.instances).toHaveLength(1);
    });

    const ws = MockWebSocket.instances[0];
    await act(async () => ws.onopen?.());

    await act(async () => {
      ws.simulateMessage(
        JSON.stringify({
          job_id: "job-1",
          brief_id: briefId,
          status: "rendering",
          phase: null,
          progress_pct: 5,
          message: null,
          timestamp: "2026-03-11T00:00:00Z",
        }),
      );
    });
    await act(async () => {
      ws.simulateMessage(
        JSON.stringify({
          job_id: "job-2",
          brief_id: briefId,
          status: "done",
          phase: null,
          progress_pct: 100,
          message: null,
          timestamp: "2026-03-11T00:00:01Z",
        }),
      );
    });

    expect(result.current.events.size).toBe(2);
    expect(result.current.events.get("job-1")?.progress_pct).toBe(5);
    expect(result.current.events.get("job-2")?.progress_pct).toBe(100);
  });

  it("closes WebSocket on unmount", async () => {
    const briefId = "abc-123";
    const { unmount } = renderHook(() => useBriefProgress(briefId));

    await vi.waitFor(() => {
      expect(MockWebSocket.instances).toHaveLength(1);
    });

    unmount();
    expect(MockWebSocket.instances[0].closeCalled).toBe(true);
  });
});
