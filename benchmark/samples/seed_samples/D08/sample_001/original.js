function findObjects(snapshot, typeName) {
  var results = [];
  var meta = snapshot.meta;
  var typeIdx = meta.node_fields.indexOf("type");
  var nameIdx = meta.node_fields.indexOf("name");
  for (var i = 0; i < snapshot.nodes.length; i += meta.node_field_count) {
    var type = meta.types[typeIdx][snapshot.nodes[i + typeIdx]];
    var name = meta.types[nameIdx][snapshot.nodes[i + nameIdx]];
    if (type === typeName) results.push({ index: i, name: name });
  }
  return results;
}
module.exports = { findObjects };
