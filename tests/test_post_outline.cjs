const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');
const vm = require('node:vm');

const script = fs.readFileSync(path.join(__dirname, '../static/assets/script/post.js'), 'utf8');

function fixture({ width = 390, hasPost = true, hasOutline = true } = {}) {
  const outline = { open: false };
  const mediaListeners = [];
  const windowListeners = new Map();
  const wideScreen = {
    matches: width >= 992,
    addEventListener(type, callback) {
      assert.equal(type, 'change');
      mediaListeners.push(callback);
    },
  };
  const post = {
    querySelector: selector => selector === '[data-post-outline]' && hasOutline ? outline : null,
    querySelectorAll: () => [],
  };
  const document = {
    querySelector: selector => selector === '.post' && hasPost ? post : null,
    querySelectorAll: () => [],
    getElementById: () => null,
  };
  const window = {
    matchMedia(query) {
      assert.equal(query, '(min-width: 992px)');
      return wideScreen;
    },
    addEventListener(type, callback) {
      const callbacks = windowListeners.get(type) || [];
      callbacks.push(callback);
      windowListeners.set(type, callbacks);
    },
  };
  vm.runInNewContext(script, { document, window });
  return {
    outline,
    resize(nextWidth) {
      const matches = nextWidth >= 992;
      if (matches !== wideScreen.matches) {
        wideScreen.matches = matches;
        mediaListeners.forEach(callback => callback({ matches }));
      }
      (windowListeners.get('resize') || []).forEach(callback => callback());
    },
  };
}

test('Outline starts folded below 992px and expanded at the desktop breakpoint', () => {
  for (const width of [320, 390, 767, 991]) {
    assert.equal(fixture({ width }).outline.open, false, `width ${width}`);
  }
  for (const width of [992, 1280]) {
    assert.equal(fixture({ width }).outline.open, true, `width ${width}`);
  }
});

test('crossing the breakpoint applies the corresponding default in both directions', () => {
  const f = fixture({ width: 991 });
  f.resize(992);
  assert.equal(f.outline.open, true);
  f.resize(991);
  assert.equal(f.outline.open, false);
  f.resize(1280);
  assert.equal(f.outline.open, true);
});

test('a reader can expand the mobile outline without same-breakpoint resizing folding it', () => {
  const f = fixture();
  f.outline.open = true;
  f.resize(480);
  f.resize(991);
  assert.equal(f.outline.open, true);
  f.resize(992);
  f.resize(991);
  assert.equal(f.outline.open, false);
});

test('a reader can fold the desktop outline until a breakpoint crossing resets it', () => {
  const f = fixture({ width: 1280 });
  f.outline.open = false;
  f.resize(1100);
  f.resize(992);
  assert.equal(f.outline.open, false);
  f.resize(991);
  f.resize(992);
  assert.equal(f.outline.open, true);
});

test('posts without an outline and pages without a post initialize safely', () => {
  assert.doesNotThrow(() => fixture({ hasOutline: false }));
  assert.doesNotThrow(() => fixture({ hasPost: false }));
});
