#!/usr/bin/env node
// Runs a candidate CommonJS module against a list of semantic test cases.
//
// Usage: node _runner.js <candidate.js> <cases.json>
//
// cases.json format:
//   { "export": "calculateDiscount",
//     "cases": [{ "name": "...", "args": [...], "expected": ... }, ...] }
//
// Output: a single JSON object on stdout with the shape:
//   { "cases": [{ "name", "passed", "actual", "expected", "error", "duration_ms" }, ...] }
//
// Each test case is executed inside a fresh `vm.Script` sandbox so the
// candidate cannot mutate the runner's globals between cases.

"use strict";

const fs = require("node:fs");
const vm = require("node:vm");

function deepEqual(a, b) {
  if (a === b) return true;
  if (typeof a !== typeof b) return false;
  if (typeof a !== "object" || a === null || b === null) {
    if (Number.isNaN(a) && Number.isNaN(b)) return true;
    return false;
  }
  if (Array.isArray(a) !== Array.isArray(b)) return false;
  if (Array.isArray(a)) {
    if (a.length !== b.length) return false;
    for (let i = 0; i < a.length; i++) {
      if (!deepEqual(a[i], b[i])) return false;
    }
    return true;
  }
  const ka = Object.keys(a);
  const kb = Object.keys(b);
  if (ka.length !== kb.length) return false;
  for (const k of ka) {
    if (!deepEqual(a[k], b[k])) return false;
  }
  return true;
}

function loadCandidate(modulePath) {
  const source = fs.readFileSync(modulePath, "utf8");
  const wrapped = `(function(module, exports){\n${source}\n;return module.exports;})`;
  const sandbox = { console: { log: () => {} }, Math, Date, JSON };
  vm.createContext(sandbox);
  const factory = vm.runInContext(wrapped, sandbox, {
    filename: "candidate.js",
    timeout: 5000,
  });
  const moduleObj = { exports: {} };
  const exportsObj = moduleObj.exports;
  return factory(moduleObj, exportsObj);
}

function runCases(candidate, exportName, cases) {
  const fn = candidate?.[exportName] ?? candidate;
  if (typeof fn !== "function") {
    return cases.map((c) => ({
      name: c.name ?? "<anon>",
      passed: false,
      expected: c.expected,
      error: `export '${exportName}' is not a function (got ${typeof fn})`,
    }));
  }
  return cases.map((c) => {
    const start = process.hrtime.bigint();
    try {
      const actual = fn(...(c.args ?? []));
      const passed = deepEqual(actual, c.expected);
      const dur = Number((process.hrtime.bigint() - start) / 1000000n);
      return {
        name: c.name ?? "<anon>",
        passed,
        actual,
        expected: c.expected,
        duration_ms: dur,
      };
    } catch (err) {
      const dur = Number((process.hrtime.bigint() - start) / 1000000n);
      return {
        name: c.name ?? "<anon>",
        passed: false,
        expected: c.expected,
        error: String(err && err.stack ? err.stack : err),
        duration_ms: dur,
      };
    }
  });
}

function main() {
  const [candidatePath, casesPath] = process.argv.slice(2);
  if (!candidatePath || !casesPath) {
    process.stderr.write("usage: _runner.js <candidate.js> <cases.json>\n");
    process.exit(2);
  }
  let exportName = "default";
  let cases = [];
  try {
    const raw = JSON.parse(fs.readFileSync(casesPath, "utf8"));
    exportName = raw.export ?? "default";
    cases = raw.cases ?? [];
  } catch (err) {
    process.stderr.write(`failed to parse cases.json: ${err}\n`);
    process.exit(3);
  }

  let candidate;
  try {
    candidate = loadCandidate(candidatePath);
  } catch (err) {
    process.stdout.write(
      JSON.stringify({
        cases: cases.map((c) => ({
          name: c.name ?? "<anon>",
          passed: false,
          expected: c.expected,
          error: `failed to load candidate: ${err && err.message ? err.message : err}`,
        })),
      })
    );
    process.exit(0);
  }

  const results = runCases(candidate, exportName, cases);
  process.stdout.write(JSON.stringify({ cases: results }));
}

main();
