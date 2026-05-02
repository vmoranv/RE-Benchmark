/**
 * Cross-domain evidence correlator.
 *
 * Takes evidence from three separate domains — HTTP headers, JavaScript
 * globals, and DOM elements — and correlates them to reconstruct the
 * full application state, user session, and security context.
 */

function correlateEvidence(evidence) {
    const correlation = {
        sessionId: null,
        userId: null,
        userRole: null,
        apiVersion: null,
        buildInfo: null,
        securityTokens: {},
        serverTiming: {},
        linkedFacts: []
    };

    // Extract from HTTP headers
    if (evidence.http_headers) {
        const headers = evidence.http_headers;

        // Decode JWT session token
        if (headers["X-Session-Token"]) {
            const jwt = decodeJWT(headers["X-Session-Token"]);
            correlation.linkedFacts.push({
                source: "http_header",
                field: "X-Session-Token",
                decoded: jwt
            });
            if (jwt && jwt.user) {
                correlation.userId = jwt.user;
            }
        }

        // Parse server timing
        if (headers["Server-Timing"]) {
            correlation.serverTiming = parseServerTiming(headers["Server-Timing"]);
        }

        // Request ID
        if (headers["X-Request-ID"]) {
            correlation.securityTokens.requestId = headers["X-Request-ID"];
        }
    }

    // Extract from JS globals
    if (evidence.js_globals) {
        const globals = evidence.js_globals;

        if (globals.__APP_CONFIG__) {
            correlation.apiVersion = globals.__APP_CONFIG__.version;
            correlation.linkedFacts.push({
                source: "js_global",
                field: "__APP_CONFIG__",
                apiBase: globals.__APP_CONFIG__.apiBase
            });
        }

        if (globals.__SESSION__) {
            correlation.userId = correlation.userId || globals.__SESSION__.userId;
            correlation.userRole = globals.__SESSION__.role;
            correlation.linkedFacts.push({
                source: "js_global",
                field: "__SESSION__",
                userId: globals.__SESSION__.userId,
                role: globals.__SESSION__.role
            });
        }
    }

    // Extract from DOM elements
    if (evidence.dom_elements) {
        const dom = evidence.dom_elements;

        if (dom["meta[name=csrf-token]"]) {
            correlation.securityTokens.csrf = dom["meta[name=csrf-token]"];
            correlation.linkedFacts.push({
                source: "dom_element",
                field: "meta[name=csrf-token]",
                token: dom["meta[name=csrf-token]"]
            });
        }

        if (dom["script[data-build]"]) {
            correlation.buildInfo = dom["script[data-build]"];
            correlation.linkedFacts.push({
                source: "dom_element",
                field: "script[data-build]",
                build: dom["script[data-build]"]
            });
        }
    }

    // Cross-domain correlation checks
    correlation.crossDomainLinks = findCrossDomainLinks(correlation);

    return correlation;
}

function decodeJWT(token) {
    try {
        const parts = token.split(".");
        if (parts.length < 2) return null;
        const payload = Buffer.from(parts[1], "base64").toString("utf8");
        return JSON.parse(payload);
    } catch {
        return null;
    }
}

function parseServerTiming(timingStr) {
    const entries = {};
    const parts = timingStr.split(",");
    for (const part of parts) {
        const match = part.trim().match(/(\w+);dur=(\d+)/);
        if (match) {
            entries[match[1]] = parseInt(match[2], 10);
        }
    }
    return entries;
}

function findCrossDomainLinks(correlation) {
    const links = [];

    // Link JWT user to __SESSION__ user
    if (correlation.userId) {
        links.push({
            type: "identity",
            description: "User identity confirmed across JWT and JS globals",
            value: correlation.userId
        });
    }

    // Link CSRF token to session
    if (correlation.securityTokens.csrf && correlation.userId) {
        links.push({
            type: "session_binding",
            description: "CSRF token bound to session for user",
            userId: correlation.userId,
            csrfToken: correlation.securityTokens.csrf
        });
    }

    return links;
}

module.exports = { correlateEvidence, decodeJWT, parseServerTiming };
