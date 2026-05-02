function parseCDPEvents(events) {
  return events.filter(function(e) { return e.method === "Runtime.consoleAPICalled"; })
    .map(function(e) { return e.params.args.map(function(a) { return a.value; }).join(" "); });
}
module.exports = { parseCDPEvents };
