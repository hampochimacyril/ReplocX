/** Resolve a CSS custom property to its computed value (charts/canvas can't read
 * CSS variables directly). Falls back when running outside a browser (tests). */
export function readVar(name: string, fallback: string): string {
  if (typeof document === "undefined") return fallback;
  const value = getComputedStyle(document.documentElement).getPropertyValue(name).trim();
  return value || fallback;
}
