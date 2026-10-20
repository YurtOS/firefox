// |jit-test| skip-if: typeof withExternalCompilerSlotPolicy !== 'function'
// Direct qualification requires the fixture; do not skip a missing hook.

for (let warm of [false, true]) {
  let source = {high: {value: 7}, low: 11};
  if (warm) {
    Object.assign({}, source);
  }
  let target = {};
  let notified = withExternalCompilerSlotPolicy(target, function () {
    Object.assign(target, source);
  });
  assertEq(notified, 2);
  assertEq(hasPermutedSlots(target), true);
  assertEq(objectSlotSpan(target), 4);
  assertEq(Object.keys(target).join(','), 'high,low');
  gc();
  assertEq(target.high.value, 7);
  assertEq(target.low, 11);
}
