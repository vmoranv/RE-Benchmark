var svc = {
  fetchData: function(url) { return fetch(url).then(function(r) { return r.json(); }); },
  postData: function(url, body) {
    var x = new XMLHttpRequest(); x.open("POST", url);
    x.setRequestHeader("Content-Type", "application/json");
    x.send(JSON.stringify(body)); return x;
  },
  genToken: function() { var b = new Uint8Array(16); crypto.getRandomValues(b); return b; },
  connect: function(url) { return new RTCPeerConnection({ iceServers: [{ urls: url }] }); }
};
module.exports = svc;
