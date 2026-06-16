/*
 * In-memory bearer-token auth for private ReplocX deployments.
 *
 * The public demo needs no token. A private instance sets RLE_PRIVATE_AUTH_TOKEN,
 * and every non-public /api route then returns 401 without an Authorization
 * header. The token is requested on demand (the first protected call) and held
 * ONLY in memory for the session — it is never written to localStorage, cookies,
 * or the URL, so a reload re-prompts. Concurrent 401s share a single prompt.
 */

let authToken: string | null = null;
let promptInFlight: Promise<string | null> | null = null;

export function getAuthToken(): string | null {
  return authToken;
}

export function setAuthToken(token: string | null): void {
  const trimmed = token?.trim();
  authToken = trimmed ? trimmed : null;
}

/** Authorization header for the current token, or `{}` when none is set. */
export function authHeaders(): Record<string, string> {
  return authToken ? { Authorization: `Bearer ${authToken}` } : {};
}

const PROMPT_MESSAGE =
  "This is a private ReplocX instance.\n\n" +
  "Paste your access token to continue. It is kept in memory for this session " +
  "only (never stored); reload the page to clear or re-enter it.";

function browserPrompt(message: string): string | null {
  if (typeof window === "undefined" || typeof window.prompt !== "function") return null;
  return window.prompt(message);
}

/**
 * Prompt the user for an access token, deduplicating concurrent callers so a
 * burst of parallel 401s shows a single prompt. Returns the newly entered token
 * (also stored via {@link setAuthToken}), or `null` if the user cancelled.
 */
export async function promptForToken(
  prompter: (message: string) => string | null = browserPrompt,
): Promise<string | null> {
  if (!promptInFlight) {
    promptInFlight = (async () => {
      const entered = prompter(PROMPT_MESSAGE);
      const token = entered?.trim() ? entered.trim() : null;
      if (token) setAuthToken(token);
      return token;
    })();
  }
  try {
    return await promptInFlight;
  } finally {
    promptInFlight = null;
  }
}
