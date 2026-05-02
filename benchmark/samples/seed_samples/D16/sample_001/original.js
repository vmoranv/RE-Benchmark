/**
 * HTTP traffic analyzer — parses captured mitmproxy-style request/response
 * pairs and extracts structured information about API interactions,
 * authentication tokens, and response data.
 */

function parseHttpPairs(rawTraffic) {
    const pairs = [];
    const blocks = rawTraffic.split(/(?=>> )/);

    for (const block of blocks) {
        const pair = parseSinglePair(block.trim());
        if (pair) pairs.push(pair);
    }

    return pairs;
}

function parseSinglePair(block) {
    if (!block.startsWith(">>")) return null;

    const lines = block.split("\n");
    const request = { method: null, path: null, version: null, headers: {} };
    const response = { status: null, statusCode: null, headers: {}, body: null };

    let section = "request";
    let bodyLines = [];

    for (const line of lines) {
        const trimmed = line.trim();

        if (section === "request") {
            if (trimmed.startsWith(">> ")) {
                // Request line: >> METHOD /path HTTP/1.1
                const parts = trimmed.substring(3).split(" ");
                request.method = parts[0];
                request.path = parts[1];
                request.version = parts[2];
            } else if (trimmed === ">>") {
                // Empty request line, skip
            } else if (trimmed.startsWith(">> ")) {
                // Additional request header
                const headerLine = trimmed.substring(3);
                const colonIdx = headerLine.indexOf(":");
                if (colonIdx !== -1) {
                    const key = headerLine.substring(0, colonIdx).trim();
                    const val = headerLine.substring(colonIdx + 1).trim();
                    request.headers[key] = val;
                }
            } else if (trimmed.startsWith("<< ")) {
                section = "response";
                // Response line: << HTTP/1.1 200 OK
                const respParts = trimmed.substring(3).split(" ");
                response.version = respParts[0];
                response.statusCode = parseInt(respParts[1], 10);
                response.status = respParts.slice(2).join(" ");
            }
        } else if (section === "response") {
            if (trimmed.startsWith("<< ")) {
                const headerLine = trimmed.substring(3);
                const colonIdx = headerLine.indexOf(":");
                if (colonIdx !== -1) {
                    const key = headerLine.substring(0, colonIdx).trim();
                    const val = headerLine.substring(colonIdx + 1).trim();
                    response.headers[key] = val;
                }
            } else if (trimmed === "<<" || trimmed === "") {
                // Skip empty separator lines
            } else {
                // Response body
                bodyLines.push(trimmed);
            }
        }
    }

    // Parse JSON body
    const bodyText = bodyLines.join("\n").trim();
    if (bodyText) {
        try {
            response.body = JSON.parse(bodyText);
        } catch {
            response.body = bodyText;
        }
    }

    return { request, response };
}

function extractAuthInfo(pairs) {
    const auth = { cookies: {}, tokens: {} };

    for (const pair of pairs) {
        const req = pair.request;

        if (req.headers["Cookie"]) {
            const cookieParts = req.headers["Cookie"].split("; ");
            for (const part of cookieParts) {
                const eqIdx = part.indexOf("=");
                if (eqIdx !== -1) {
                    const key = part.substring(0, eqIdx);
                    const val = part.substring(eqIdx + 1);
                    auth.cookies[key] = val;
                }
            }
        }

        if (req.headers["Authorization"]) {
            const authHeader = req.headers["Authorization"];
            if (authHeader.startsWith("Bearer ")) {
                auth.tokens.bearer = authHeader.substring(7);
            }
        }
    }

    return auth;
}

function extractUserData(pairs) {
    for (const pair of pairs) {
        if (pair.response.body && typeof pair.response.body === "object") {
            return pair.response.body;
        }
    }
    return null;
}

module.exports = { parseHttpPairs, parseSinglePair, extractAuthInfo, extractUserData };
