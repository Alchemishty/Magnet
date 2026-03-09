import { describe, it, expect } from 'vitest';

describe('Sanity check', () => {
  it('verifies 1 + 1 = 2', () => {
    // Arrange
    const a = 1;
    const b = 1;

    // Act
    const result = a + b;

    // Assert
    expect(result).toBe(2);
  });
});
