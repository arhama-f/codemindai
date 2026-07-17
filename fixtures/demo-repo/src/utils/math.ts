export function add(a: number, b: number): number {
  return a + b;
}

export function subtract(a: number, b: number): number {
  return a - b;
}

export function multiply(a: number, b: number): number {
  return a * b;
}

// BUG: no zero-check before dividing — planted for a later bug-detection phase.
export function divide(a: number, b: number): number {
  return a / b;
}
