function disasm(hexBytes) {
  var ops = { "01": "add", "29": "sub", "50": "push rax", "58": "pop rax", "c3": "ret", "89": "mov", "b8": "mov eax,imm32" };
  var result = [];
  for (var i = 0; i < hexBytes.length; i += 2) {
    var b = hexBytes.substr(i, 2);
    result.push({ offset: "0x" + (i / 2).toString(16), bytes: b, mnemonic: ops[b] || "???" });
  }
  return result;
}
module.exports = { disasm };
