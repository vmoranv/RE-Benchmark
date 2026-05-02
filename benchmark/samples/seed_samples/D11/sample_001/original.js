function parseSyscalls(trace) {
  return trace.split("\n").filter(function(l) { return l.includes("openat") || l.includes("read"); })
    .map(function(l) {
      var m = l.match(/openat\([^,]+,\s*"([^"]+)"/) || l.match(/read\(\d+,\s*"([^"]+)"/);
      return m ? m[1] : null;
    }).filter(Boolean);
}
module.exports = { parseSyscalls };
