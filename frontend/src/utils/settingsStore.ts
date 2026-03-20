/**
 * Browser-based settings store using localStorage.
 * Synchronous replacement for Tauri's plugin-store.
 */

const STORAGE_PREFIX = "openaec-settings:";

export function getSetting<T>(key: string, fallback: T): T {
  try {
    const raw = localStorage.getItem(STORAGE_PREFIX + key);
    if (raw === null) return fallback;
    return JSON.parse(raw) as T;
  } catch {
    return fallback;
  }
}

export function setSetting<T>(key: string, value: T): void {
  try {
    localStorage.setItem(STORAGE_PREFIX + key, JSON.stringify(value));
  } catch {
    // localStorage not available or quota exceeded
  }
}
