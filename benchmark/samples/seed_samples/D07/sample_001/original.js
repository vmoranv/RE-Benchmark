function renderScene(ctx) {
  var shapes = [
    { type: "rect", x: 10, y: 10, w: 80, h: 60, color: "#e74c3c" },
    { type: "circle", x: 200, y: 100, r: 40, color: "#3498db" },
    { type: "rect", x: 300, y: 50, w: 100, h: 80, color: "#2ecc71" }
  ];
  shapes.forEach(function(s) {
    ctx.fillStyle = s.color;
    if (s.type === "rect") { ctx.fillRect(s.x, s.y, s.w, s.h); }
    else { ctx.beginPath(); ctx.arc(s.x, s.y, s.r, 0, Math.PI * 2); ctx.fill(); }
  });
}
module.exports = { renderScene };
