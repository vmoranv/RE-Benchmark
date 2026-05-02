function extractJA3(clientHello) {
    var version = clientHello.version;
    var ciphers = clientHello.cipherSuites.join("-");
    var extensions = clientHello.extensions.map(function(e) { return e.type; }).join("-");
    var curves = clientHello.extensions.filter(function(e) { return e.type === 10; })
        .map(function(e) { return e.data.join("-"); }).join("-");
    var pointFormats = clientHello.extensions.filter(function(e) { return e.type === 11; })
        .map(function(e) { return e.data.join("-"); }).join("-");
    return [version, ciphers, extensions, curves, pointFormats].join(",");
}
module.exports = { extractJA3 };
