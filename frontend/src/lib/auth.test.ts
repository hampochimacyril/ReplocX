import { describe, it, expect, beforeEach } from "vitest";
import { authHeaders, getAuthToken, promptForToken, setAuthToken } from "./auth";

describe("in-memory auth token store", () => {
  beforeEach(() => setAuthToken(null));

  it("attaches the proxy-compatible app-token header only when a token is set", () => {
    expect(authHeaders()).toEqual({});
    setAuthToken("abc123");
    expect(authHeaders()).toEqual({ "X-RLE-Auth": "abc123" });
  });

  it("trims whitespace and treats blank tokens as unset", () => {
    setAuthToken("  spaced  ");
    expect(getAuthToken()).toBe("spaced");
    setAuthToken("   ");
    expect(getAuthToken()).toBeNull();
  });

  it("stores the entered token and dedupes concurrent prompts", async () => {
    let calls = 0;
    const prompter = () => {
      calls += 1;
      return "tok-123";
    };
    const [a, b] = await Promise.all([promptForToken(prompter), promptForToken(prompter)]);
    expect(a).toBe("tok-123");
    expect(b).toBe("tok-123");
    expect(calls).toBe(1); // a single shared prompt for concurrent 401s
    expect(getAuthToken()).toBe("tok-123");
  });

  it("returns null and leaves the token unset when the user cancels", async () => {
    const token = await promptForToken(() => null);
    expect(token).toBeNull();
    expect(getAuthToken()).toBeNull();
  });
});
