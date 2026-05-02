/**
 * Hex memory dump scanner — finds patterns and reconstructs data structures
 * from a hex-and-ASCII memory dump (similar to xxd/hexdump output).
 *
 * The dump format is:
 *   OFFSET: XXXX XXXX XXXX XXXX XXXX XXXX XXXX XXXX  ASCII...........
 *
 * Structures embedded in the dump:
 *   Offset 0x00: 16-byte null-terminated string (name)
 *   Offset 0x10: 3 x uint32 LE fields (age, score, flags)
 *   Offset 0x20: 16-byte null-terminated string (username)
 *   Offset 0x30: 16-byte null-terminated string (role)
 *   Offset 0x40: uint64 LE (balance in cents)
 */

function parseHexDump(dumpText) {
    const lines = dumpText.trim().split("\n");
    const segments = [];

    for (const line of lines) {
        const parsed = parseDumpLine(line);
        if (parsed) segments.push(parsed);
    }

    return reconstructStructures(segments);
}

function parseDumpLine(line) {
    // Match: "OFFSET: XXXX XXXX XXXX XXXX XXXX XXXX XXXX XXXX  ASCII"
    const re = /^([0-9a-f]+):\s+((?:[0-9a-f]{4}\s+){8})\s+(.+)$/;
    const match = line.match(re);
    if (!match) return null;

    const offset = parseInt(match[1], 16);
    const hexPart = match[2].trim();
    const asciiPart = match[3].trim();

    // Convert hex groups to bytes
    const bytes = [];
    const groups = hexPart.split(/\s+/);
    for (const group of groups) {
        bytes.push(parseInt(group.substr(0, 2), 16));
        bytes.push(parseInt(group.substr(2, 2), 16));
    }

    return { offset, bytes, ascii: asciiPart };
}

function reconstructStructures(segments) {
    const result = {
        rawSegments: segments,
        structures: {}
    };

    // Flatten all bytes into a single buffer
    const buffer = new Uint8Array(256);
    for (const seg of segments) {
        for (let i = 0; i < seg.bytes.length; i++) {
            buffer[seg.offset + i] = seg.bytes[i];
        }
    }

    // Extract name string at offset 0x00 (16 bytes, null-terminated)
    result.structures.name = extractString(buffer, 0x00, 16);

    // Extract fields at offset 0x10
    result.structures.age = readUint32LE(buffer, 0x10);
    result.structures.score = readUint32LE(buffer, 0x14);
    result.structures.flags = readUint32LE(buffer, 0x18);

    // Extract username at offset 0x20
    result.structures.username = extractString(buffer, 0x20, 16);

    // Extract role at offset 0x30
    result.structures.role = extractString(buffer, 0x30, 16);

    // Extract balance at offset 0x40
    result.structures.balance = readUint32LE(buffer, 0x40);

    return result;
}

function extractString(buffer, offset, maxLen) {
    let str = "";
    for (let i = 0; i < maxLen; i++) {
        const byte = buffer[offset + i];
        if (byte === 0) break;
        str += String.fromCharCode(byte);
    }
    return str;
}

function readUint32LE(buffer, offset) {
    return (
        buffer[offset] |
        (buffer[offset + 1] << 8) |
        (buffer[offset + 2] << 16) |
        (buffer[offset + 3] << 24)
    ) >>> 0;
}

module.exports = { parseHexDump, parseDumpLine, reconstructStructures };
