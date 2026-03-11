import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { apiGet, apiPost, apiPatch, apiDelete, ApiError } from "@/lib/api/client";

const TEST_API_URL = "http://test-api:9000";

function mockFetchOk(data: unknown) {
  return vi.fn().mockResolvedValue({
    ok: true,
    json: () => Promise.resolve(data),
    text: () => Promise.resolve(""),
  });
}

function mockFetchError(status: number, body: string) {
  return vi.fn().mockResolvedValue({
    ok: false,
    status,
    json: () => Promise.resolve(null),
    text: () => Promise.resolve(body),
  });
}

beforeEach(() => {
  vi.stubGlobal("process", {
    env: { NEXT_PUBLIC_API_URL: TEST_API_URL },
  });
});

afterEach(() => {
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
});

describe("apiGet", () => {
  it("calls fetch with correct URL and returns parsed JSON", async () => {
    const data = { id: "1", name: "Test" };
    const fetchMock = mockFetchOk(data);
    vi.stubGlobal("fetch", fetchMock);

    const result = await apiGet("/api/projects");

    expect(fetchMock).toHaveBeenCalledWith(`${TEST_API_URL}/api/projects`);
    expect(result).toEqual(data);
  });

  it("throws ApiError with status and message on non-ok response", async () => {
    const fetchMock = mockFetchError(404, "Not Found");
    vi.stubGlobal("fetch", fetchMock);

    const error = await apiGet("/api/projects/999").catch((e) => e);
    expect(error).toBeInstanceOf(ApiError);
    expect(error).toMatchObject({ status: 404, message: "Not Found" });
  });
});

describe("apiPost", () => {
  it("calls fetch with POST method, JSON headers, and stringified body", async () => {
    const responseData = { id: "1", name: "New" };
    const requestBody = { name: "New" };
    const fetchMock = mockFetchOk(responseData);
    vi.stubGlobal("fetch", fetchMock);

    const result = await apiPost("/api/projects", requestBody);

    expect(fetchMock).toHaveBeenCalledWith(`${TEST_API_URL}/api/projects`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(requestBody),
    });
    expect(result).toEqual(responseData);
  });

  it("throws ApiError on non-ok response", async () => {
    const fetchMock = mockFetchError(422, "Validation Error");
    vi.stubGlobal("fetch", fetchMock);

    const error = await apiPost("/api/projects", {}).catch((e) => e);
    expect(error).toBeInstanceOf(ApiError);
    expect(error).toMatchObject({ status: 422, message: "Validation Error" });
  });
});

describe("apiPatch", () => {
  it("calls fetch with PATCH method, JSON headers, and stringified body", async () => {
    const responseData = { id: "1", name: "Updated" };
    const requestBody = { name: "Updated" };
    const fetchMock = mockFetchOk(responseData);
    vi.stubGlobal("fetch", fetchMock);

    const result = await apiPatch("/api/projects/1", requestBody);

    expect(fetchMock).toHaveBeenCalledWith(`${TEST_API_URL}/api/projects/1`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(requestBody),
    });
    expect(result).toEqual(responseData);
  });

  it("throws ApiError on non-ok response", async () => {
    const fetchMock = mockFetchError(500, "Internal Server Error");
    vi.stubGlobal("fetch", fetchMock);

    const error = await apiPatch("/api/projects/1", {}).catch((e) => e);
    expect(error).toBeInstanceOf(ApiError);
    expect(error).toMatchObject({ status: 500, message: "Internal Server Error" });
  });
});

describe("apiDelete", () => {
  it("calls fetch with DELETE method", async () => {
    const fetchMock = mockFetchOk(undefined);
    vi.stubGlobal("fetch", fetchMock);

    await apiDelete("/api/projects/1");

    expect(fetchMock).toHaveBeenCalledWith(`${TEST_API_URL}/api/projects/1`, {
      method: "DELETE",
    });
  });

  it("throws ApiError on non-ok response", async () => {
    const fetchMock = mockFetchError(403, "Forbidden");
    vi.stubGlobal("fetch", fetchMock);

    const error = await apiDelete("/api/projects/1").catch((e) => e);
    expect(error).toBeInstanceOf(ApiError);
    expect(error).toMatchObject({ status: 403, message: "Forbidden" });
  });
});
