import axios from "axios";

/** Empty = same-origin (Docker :8080 or Vite :5173 with proxy). */
const apiBase = (import.meta.env.VITE_API_URL ?? "").replace(/\/$/, "");

export const api = axios.create({
  baseURL: `${apiBase}/api`,
  timeout: 60_000,
});

export function authHeader(token: string | null) {
  return token ? { Authorization: `Bearer ${token}` } : {};
}

/**
 * Resolve API image paths to a browser-loadable URL.
 * Uses window.location.origin when VITE_API_URL is unset so screenshots work on :8080 and :5173.
 */
export function resolveAssetUrl(pathOrUrl: string): string {
  if (!pathOrUrl?.trim()) return "";
  let trimmed = pathOrUrl.trim();
  const pageOrigin =
    typeof window !== "undefined" ? window.location.origin : apiBase || "";

  // API may return http://localhost:8080/... while UI runs on :5173 — always use current tab origin.
  if (pageOrigin && (trimmed.startsWith("http://") || trimmed.startsWith("https://"))) {
    try {
      const u = new URL(trimmed);
      if (u.pathname.startsWith("/support-assets/") || u.pathname.startsWith("/demo-assets/")) {
        trimmed = `${pageOrigin}${u.pathname}${u.search}`;
      }
    } catch {
      /* keep original */
    }
    return trimmed;
  }

  const origin = apiBase || pageOrigin;
  const path = trimmed.startsWith("/") ? trimmed : `/${trimmed}`;
  const resolved = `${origin}${path}`;
  if (typeof window !== "undefined") {
    console.info("[IMAGE] Resolved URL:", resolved);
  }
  return resolved;
}
