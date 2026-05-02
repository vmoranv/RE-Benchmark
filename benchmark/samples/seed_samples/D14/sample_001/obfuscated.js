// Captured execution trace — reconstruct the call flow and return values.
var _0xe=[
  {"ts":0,"op":"call","fn":"init","args":[]},
  {"ts":1,"op":"call","fn":"loadConfig","args":["/api/config"]},
  {"ts":3,"op":"return","fn":"loadConfig","val":{"theme":"dark"}},
  {"ts":5,"op":"call","fn":"render","args":["dark"]},
  {"ts":8,"op":"call","fn":"applyTheme","args":["dark"]},
  {"ts":10,"op":"return","fn":"applyTheme","val":true},
  {"ts":11,"op":"return","fn":"render","val":null},
  {"ts":12,"op":"return","fn":"init","val":"ok"}
];
