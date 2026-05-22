/** Normalize support-flow open_url / navigation path for React Router. */
export function normalizeDemoPath(url: string | null | undefined): string | null {
  if (!url?.trim()) return null;
  let p = url.trim();
  if (p.startsWith("#")) p = p.slice(1);
  if (!p.startsWith("/")) p = `/${p}`;
  return p.split("?")[0] || null;
}

export function openPageLabel(path: string): string {
  const segment = path.split("/").filter(Boolean).pop() ?? "page";
  return segment.replace(/-/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}
