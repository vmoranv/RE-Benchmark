/**
 * Execution trace replay engine.
 *
 * Takes a JSON execution trace (array of call/return events) and
 * reconstructs the full execution flow including call stack state
 * at each point in time.
 */

function replayTrace(trace) {
    const stack = [];
    const timeline = [];
    const callGraph = {};

    for (const event of trace) {
        const entry = {
            timestamp: event.ts,
            stackDepth: stack.length,
            event: event
        };

        if (event.op === "call") {
            stack.push({
                fn: event.fn,
                args: event.args,
                callTs: event.ts
            });

            // Record in call graph
            const caller = stack.length > 1
                ? stack[stack.length - 2].fn
                : "<root>";
            if (!callGraph[caller]) {
                callGraph[caller] = [];
            }
            callGraph[caller].push(event.fn);

            entry.action = "push";
            entry.currentStack = stack.map(s => s.fn);
        } else if (event.op === "return") {
            // Find matching call on stack
            const callIdx = stack.findIndex(s => s.fn === event.fn);
            if (callIdx !== -1) {
                const call = stack[callIdx];
                entry.duration = event.ts - call.callTs;
                entry.returnValue = event.val;
                stack.splice(callIdx, 1);
            }

            entry.action = "pop";
            entry.currentStack = stack.map(s => s.fn);
        }

        timeline.push(entry);
    }

    return {
        timeline,
        callGraph,
        finalStack: stack.map(s => s.fn),
        totalDuration: trace.length > 0
            ? trace[trace.length - 1].ts - trace[0].ts
            : 0
    };
}

function extractCallOrder(trace) {
    return trace
        .filter(e => e.op === "call")
        .map(e => e.fn);
}

function extractReturnValues(trace) {
    return trace
        .filter(e => e.op === "return")
        .map(e => ({ fn: e.fn, value: e.val }));
}

function reconstructSource(trace) {
    const indent = (depth) => "  ".repeat(depth);
    let depth = 0;
    let source = "";

    for (const event of trace) {
        if (event.op === "call") {
            const args = JSON.stringify(event.args).slice(1, -1);
            source += `${indent(depth)}${event.fn}(${args}) {\n`;
            depth++;
        } else if (event.op === "return") {
            depth = Math.max(0, depth - 1);
            const retStr = event.val !== null
                ? ` // returns ${JSON.stringify(event.val)}`
                : "";
            source += `${indent(depth)}}${retStr}\n`;
        }
    }

    return source;
}

module.exports = { replayTrace, extractCallOrder, extractReturnValues, reconstructSource };
