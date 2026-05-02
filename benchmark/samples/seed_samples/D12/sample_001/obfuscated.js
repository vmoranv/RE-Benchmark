// Captured WebSocket traffic — hex-encoded raw frames from a browser session.
// Reconstruct the state machine and decode each frame's payload.
const _0xf = [
  "810748656c6c6f21",   // FIN text, len=7
  "8205776f726c64",     // FIN binary, len=5
  "8183626174",         // FIN text masked, len=3, mask=626174 -> unmasked
  "800470696e67",       // FIN continuation, len=4
  "8800"                // FIN close, len=0
];
