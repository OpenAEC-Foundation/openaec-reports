/**
 * PKCE (Proof Key for Code Exchange) utility voor OAuth2 Authorization Code flow.
 *
 * Gebruikt native Web Crypto API — geen externe dependencies.
 */

/** Genereer een cryptografisch random string voor code_verifier. */
function generateRandomString(length: number): string {
  const charset = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-._~";
  const array = new Uint8Array(length);
  crypto.getRandomValues(array);
  return Array.from(array, (byte) => charset[byte % charset.length]).join("");
}

/** Base64url-encode een ArrayBuffer (geen padding). */
function base64UrlEncode(buffer: ArrayBuffer): string {
  const bytes = new Uint8Array(buffer);
  let binary = "";
  for (const byte of bytes) {
    binary += String.fromCharCode(byte);
  }
  return btoa(binary).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
}

/** Bereken SHA-256 hash van een string. */
async function sha256(plain: string): Promise<ArrayBuffer> {
  const encoder = new TextEncoder();
  const data = encoder.encode(plain);
  return crypto.subtle.digest("SHA-256", data);
}

export interface PkceChallenge {
  codeVerifier: string;
  codeChallenge: string;
  codeChallengeMethod: "S256";
}

/**
 * Genereer een PKCE code verifier + challenge pair.
 *
 * De code_verifier wordt opgeslagen in sessionStorage en na gebruik verwijderd.
 */
export async function generatePkceChallenge(): Promise<PkceChallenge> {
  const codeVerifier = generateRandomString(64);
  const hash = await sha256(codeVerifier);
  const codeChallenge = base64UrlEncode(hash);

  return {
    codeVerifier,
    codeChallenge,
    codeChallengeMethod: "S256",
  };
}

const STORAGE_KEY = "openaec_pkce_verifier";
const STATE_KEY = "openaec_oidc_state";

/** Sla code verifier op in sessionStorage. */
export function storePkceVerifier(verifier: string): void {
  sessionStorage.setItem(STORAGE_KEY, verifier);
}

/** Haal code verifier op uit sessionStorage en verwijder het. */
export function consumePkceVerifier(): string | null {
  const verifier = sessionStorage.getItem(STORAGE_KEY);
  sessionStorage.removeItem(STORAGE_KEY);
  return verifier;
}

/** Genereer en sla een random state parameter op. */
export function generateState(): string {
  const state = generateRandomString(32);
  sessionStorage.setItem(STATE_KEY, state);
  return state;
}

/** Valideer en consumeer de state parameter. */
export function validateState(receivedState: string): boolean {
  const storedState = sessionStorage.getItem(STATE_KEY);
  sessionStorage.removeItem(STATE_KEY);
  return storedState === receivedState;
}
