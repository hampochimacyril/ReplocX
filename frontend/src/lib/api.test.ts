import { describe, it, expect, beforeEach, afterEach, vi } from "vitest";
import { api } from "./api";
import { setAuthToken } from "./auth";

function fakeResponse(status: number, body: unknown) {
  return {
    ok: status >= 200 && status < 300,
    status,
    text: async () => JSON.stringify(body),
  } as Response;
}

describe("api client auth handling", () => {
  beforeEach(() => setAuthToken(null));
  afterEach(() => {
    vi.restoreAllMocks();
    vi.unstubAllGlobals();
    setAuthToken(null);
  });

  it("prompts for a token on 401 and retries with the bearer header", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(fakeResponse(401, { error: "Authentication required for this private API route." }))
      .mockResolvedValueOnce(fakeResponse(200, { kpis: { target_strata: 20 } }));
    vi.stubGlobal("fetch", fetchMock);
    vi.spyOn(window, "prompt").mockReturnValue("secret-token");

    const data = await api.dashboard();

    expect(data).toEqual({ kpis: { target_strata: 20 } });
    expect(fetchMock).toHaveBeenCalledTimes(2);
    const firstHeaders = (fetchMock.mock.calls[0][1] as RequestInit).headers as Record<string, string>;
    const secondHeaders = (fetchMock.mock.calls[1][1] as RequestInit).headers as Record<string, string>;
    expect(firstHeaders.Authorization).toBeUndefined();
    expect(secondHeaders.Authorization).toBe("Bearer secret-token");
  });

  it("does not send an Authorization header when no token is set (public demo)", async () => {
    const fetchMock = vi.fn().mockResolvedValueOnce(fakeResponse(200, { status: "ok" }));
    vi.stubGlobal("fetch", fetchMock);

    await api.health();

    expect(fetchMock).toHaveBeenCalledTimes(1);
    const headers = (fetchMock.mock.calls[0][1] as RequestInit).headers as Record<string, string>;
    expect(headers.Authorization).toBeUndefined();
  });

  it("surfaces the 401 message when the user cancels the prompt", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValue(fakeResponse(401, { error: "Authentication required for this private API route." }));
    vi.stubGlobal("fetch", fetchMock);
    vi.spyOn(window, "prompt").mockReturnValue(null);

    await expect(api.dashboard()).rejects.toThrowError(/Authentication required/);
  });
});
