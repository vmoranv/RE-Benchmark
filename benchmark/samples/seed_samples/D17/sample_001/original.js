/**
 * Factorial function — clean reference implementation.
 *
 * Computes n! using an iterative approach to avoid stack overflow
 * for large values of n.
 *
 * @param {number} n - Non-negative integer
 * @returns {number} n!
 */
function factorial(n) {
    if (n < 0) {
        throw new RangeError("n must be non-negative");
    }
    if (n === 0 || n === 1) {
        return 1;
    }
    let result = 1;
    for (let i = 2; i <= n; i++) {
        result *= i;
    }
    return result;
}

module.exports = { factorial };
