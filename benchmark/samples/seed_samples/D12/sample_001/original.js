/**
 * WebSocket protocol frame parser.
 *
 * Decodes raw binary WebSocket frames per RFC 6455 and reconstructs
 * the state machine transitions for a captured session.
 *
 * Frame format:
 *   Byte 0: FIN bit (0x80) + opcode (0x0-0xF)
 *   Byte 1: MASK bit (0x80) + payload length (7 bits or extended)
 *   Following bytes: mask key (4 bytes if masked) then payload
 */

const OPCODES = {
    0x0: "continuation",
    0x1: "text",
    0x2: "binary",
    0x8: "close",
    0x9: "ping",
    0xA: "pong"
};

function decodeFrame(hexString) {
    const bytes = hexToBytes(hexString);
    if (bytes.length < 2) return null;

    const byte0 = bytes[0];
    const byte1 = bytes[1];

    const fin = (byte0 & 0x80) !== 0;
    const opcode = byte0 & 0x0F;
    const masked = (byte1 & 0x80) !== 0;
    let payloadLen = byte1 & 0x7F;

    let offset = 2;

    // Extended payload length
    if (payloadLen === 126) {
        payloadLen = (bytes[offset] << 8) | bytes[offset + 1];
        offset += 2;
    } else if (payloadLen === 127) {
        payloadLen = 0;
        for (let i = 0; i < 8; i++) {
            payloadLen = (payloadLen << 8) | bytes[offset + i];
        }
        offset += 8;
    }

    // Masking key
    let maskKey = null;
    if (masked) {
        maskKey = bytes.slice(offset, offset + 4);
        offset += 4;
    }

    // Payload
    const payload = bytes.slice(offset, offset + payloadLen);

    // Unmask if needed
    const decodedPayload = masked ? unmask(payload, maskKey) : payload;

    const typeName = OPCODES[opcode] || "unknown";

    return {
        fin,
        opcode,
        type: typeName,
        masked,
        payloadLength: payloadLen,
        payload: typeName === "text" || typeName === "continuation"
            ? bytesToString(decodedPayload)
            : bytesToHex(decodedPayload)
    };
}

function decodeSession(frameArray) {
    const transitions = [];
    let prevState = "CONNECTED";

    for (const hex of frameArray) {
        const frame = decodeFrame(hex);
        if (!frame) continue;

        const nextState = getStateTransition(prevState, frame);
        transitions.push({
            from: prevState,
            to: nextState,
            frame: frame
        });
        prevState = nextState;
    }

    return transitions;
}

function getStateTransition(currentState, frame) {
    switch (frame.type) {
        case "text":
        case "binary":
        case "continuation":
            return "MESSAGE";
        case "ping":
            return "PING_SENT";
        case "pong":
            return "PONG_SENT";
        case "close":
            return "CLOSED";
        default:
            return currentState;
    }
}

function hexToBytes(hex) {
    const bytes = [];
    for (let i = 0; i < hex.length; i += 2) {
        bytes.push(parseInt(hex.substr(i, 2), 16));
    }
    return bytes;
}

function unmask(payload, maskKey) {
    const result = [];
    for (let i = 0; i < payload.length; i++) {
        result.push(payload[i] ^ maskKey[i % 4]);
    }
    return result;
}

function bytesToString(bytes) {
    return String.fromCharCode.apply(null, bytes);
}

function bytesToHex(bytes) {
    return bytes.map(b => b.toString(16).padStart(2, "0")).join("");
}

module.exports = { decodeFrame, decodeSession, hexToBytes, OPCODES };
