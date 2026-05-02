function calculatePrice(base, tax, discount) { return base * (1 + tax) - discount; }
module.exports = { calculatePrice };
