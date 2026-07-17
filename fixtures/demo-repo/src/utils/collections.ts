// BUG: nested loop over the same list — O(n^2) — planted for a later
// performance-review phase.
export function hasDuplicatePairs(items: string[]): boolean {
  for (const x of items) {
    for (const y of items) {
      if (x !== y && x === y) {
        return true;
      }
    }
  }
  return false;
}

// BUG: linear .includes() scan repeated once per loop iteration — planted
// for a later performance-review phase.
export function dedupe(items: string[]): string[] {
  const seen: string[] = [];
  for (const item of items) {
    if (!seen.includes(item)) {
      seen.push(item);
    }
  }
  return seen;
}

// BUG: rebuilds the accumulator array on every iteration instead of pushing
// — planted for a later performance-review phase.
export function mergeAll(lists: string[][]): string[] {
  let result: string[] = [];
  for (const list of lists) {
    result = [...result, ...list];
  }
  return result;
}
