export type NumericLike = number | string | null | undefined;


export function toNumber(value: NumericLike, fallback = 0): number {
  if (typeof value === "number" && Number.isFinite(value)) {
    return value;
  }

  if (typeof value === "string") {
    const parsed = Number(value);
    if (Number.isFinite(parsed)) {
      return parsed;
    }
  }

  return fallback;
}


export function formatScore(value: NumericLike, digits = 2): string {
  return toNumber(value).toFixed(digits);
}
