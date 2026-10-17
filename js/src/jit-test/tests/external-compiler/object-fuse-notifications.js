// |jit-test| skip-if: typeof observeExternalCompilerFuse !== 'function'
// Run directly in external-hook qualification so missing support is an error.

let value = {method: function () { return 1; }};
let slots = observeExternalCompilerFuse(value, function () {
  value.method = function () { return 2; };
});
assertEq(slots.includes(0), true);
assertEq(value.method(), 2);

let proto = {method: function () { return 3; }};
let child = Object.create(proto);
slots = observeExternalCompilerFuse(proto, function () {
  Object.setPrototypeOf(proto, {inherited: 4});
});
assertEq(slots.includes(4294967295), true);
assertEq(proto.inherited, 4);
assertEq(child.inherited, 4);

let removed = {method: function () { return 5; }};
slots = observeExternalCompilerFuse(removed, function () {
  delete removed.method;
});
assertEq(slots.includes(0), true);
assertEq('method' in removed, false);

let stable = {method: function () { return 6; }};
slots = observeExternalCompilerFuse(stable, function () {
  gc();
  assertEq(stable.method(), 6);
});
assertEq(slots.length, 0);
