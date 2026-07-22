import { divide } from "./math";

describe("divide", () => {
  it("divides two non-zero numbers correctly", () => {
    expect(divide(10, 2)).toBe(5);
  });

  it("handles negative numbers", () => {
    expect(divide(-10, 2)).toBe(-5);
  });

  it("throws an error when dividing by zero", () => {
    expect(() => divide(10, 0)).toThrow("Division by zero is not allowed.");
  });

  it("throws an error when dividing zero by zero", () => {
    expect(() => divide(0, 0)).toThrow("Division by zero is not allowed.");
  });
});
