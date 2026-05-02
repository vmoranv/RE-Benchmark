// x86-64 function: add(a, b) -> a + b
// Function signature: int64_t add(int64_t a, int64_t b)
var _0xhex = "89f801d0c3";
// Hex bytes: 89 f8 = mov eax, edi | 01 d0 = add eax, edx | c3 = ret
// ABI: rdi=a, rdx=b, result in eax
module.exports = { rawHex: _0xhex, signature: "int64_t(int64_t,int64_t)" };
