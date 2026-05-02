// Captured HTTP traffic from mitmproxy — parse request/response pairs.
var _0xt = `>> GET /api/v2/users/me HTTP/1.1
>> Host: app.example.com
>> Cookie: session=s%3Aabc123.def456
>> Authorization: Bearer eyJhbGciOiJub25lIn0.eyJ1c2VyIjoiYWRtaW4ifQ.
>>
<< HTTP/1.1 200 OK
<< Content-Type: application/json
<< X-Request-Id: req-7f8a9b
<< {"id":"usr_001","name":"Admin","role":"superadmin","permissions":["read","write","delete"]}`;
