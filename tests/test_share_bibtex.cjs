const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');
const vm = require('node:vm');

const shareScript = fs.readFileSync(path.join(__dirname, '../static/assets/script/share.js'), 'utf8');
const postScript = fs.readFileSync(path.join(__dirname, '../static/assets/script/post.js'), 'utf8');
const bibtex = '@article{example,\n  title = {A < B & C},\n  author = {Example, Person}\n}';

function element() {
  const listeners = new Map();
  const attributes = new Map();
  return {
    hidden: true,
    disabled: false,
    textContent: '',
    focusCount: 0,
    classList: new Set(),
    setAttribute(name, value) { attributes.set(name, value); },
    getAttribute(name) { return attributes.get(name); },
    addEventListener(type, callback) {
      const callbacks = listeners.get(type) || [];
      callbacks.push(callback);
      listeners.set(type, callbacks);
    },
    async emit(type, properties = {}) {
      const event = { target: this, preventDefault() { this.defaultPrevented = true; }, ...properties };
      await Promise.all((listeners.get(type) || []).map(callback => callback(event)));
      return event;
    },
    querySelector() { return null; },
    closest() { return null; },
    focus() { this.focusCount += 1; },
  };
}

function fixture({ hasCitation = true, clipboard = 'success', deferReady = false } = {}) {
  const document = element();
  const share = element();
  const menu = element();
  const toggle = element();
  const shareStatus = element();
  const citationStatus = element();
  const menuCopy = element();
  const citationCopy = element();
  const pre = element();
  const citation = { textContent: ` \n${bibtex}\n `, parentElement: pre };
  const writes = [];
  const selection = {
    ranges: [],
    removeAllRanges() { this.ranges = []; },
    addRange(range) { this.ranges.push(range); },
  };
  const copies = hasCitation ? [menuCopy, citationCopy] : [];
  menu.hidden = false; // Static links are usable before enhancement.
  share.querySelector = selector => ({
    '[data-share-toggle]': toggle,
    '.share-menu': menu,
    "[role='status']": shareStatus,
    '[role="status"]': shareStatus,
  })[selector] || null;
  share.contains = target => [share, toggle, menu, menuCopy, shareStatus].includes(target);
  menuCopy.closest = selector => selector === '[data-share]' ? share : null;
  pre.focus = () => {
    pre.focusCount += 1;
    share.emit('focusout', { relatedTarget: pre });
  };
  document.readyState = deferReady ? 'loading' : 'complete';
  document.querySelector = selector => selector === '[data-copy-status]' && hasCitation ? citationStatus : null;
  document.querySelectorAll = selector => ({
    '[data-share]': [share],
    '[data-copy-citation]': copies,
  })[selector] || [];
  document.getElementById = id => id === 'post-bibtex' && hasCitation ? citation : null;
  document.createRange = () => ({ selectNodeContents(node) { this.node = node; } });
  const navigator = {};
  if (clipboard !== 'unavailable') {
    navigator.clipboard = { async writeText(value) {
      writes.push(value);
      if (typeof clipboard === 'function') await clipboard();
      if (clipboard === 'denied') throw new Error('Permission denied');
    } };
  }
  const context = { document, navigator, window: { getSelection: () => selection } };
  vm.runInNewContext(shareScript, context);
  vm.runInNewContext(postScript, context);
  return { document, share, menu, toggle, shareStatus, citationStatus, menuCopy,
    citationCopy, pre, citation, copies, writes, selection };
}

test('Share works without a copy action, including Escape and outside/focus dismissal', async () => {
  const f = fixture({ hasCitation: false });
  assert.equal(f.toggle.hidden, false);
  assert.equal(f.menu.hidden, true);
  assert.equal(f.share.classList.has('share--enhanced'), true);
  await f.toggle.emit('click');
  assert.equal(f.menu.hidden, false);
  assert.equal(f.toggle.getAttribute('aria-expanded'), 'true');
  const escape = await f.share.emit('keydown', { key: 'Escape' });
  assert.equal(escape.defaultPrevented, true);
  assert.equal(f.menu.hidden, true);
  assert.equal(f.toggle.focusCount, 1);
  await f.toggle.emit('click');
  await f.document.emit('click', { target: f.menu });
  assert.equal(f.menu.hidden, false);
  await f.document.emit('click', { target: element() });
  assert.equal(f.menu.hidden, true);
  await f.toggle.emit('click');
  await f.share.emit('focusout', { relatedTarget: element() });
  assert.equal(f.menu.hidden, true);
});

test('Share also initializes without a citation when loaded before DOMContentLoaded', async () => {
  const f = fixture({ hasCitation: false, deferReady: true });
  assert.equal(f.toggle.hidden, true);
  assert.equal(f.menu.hidden, false);
  await f.document.emit('DOMContentLoaded');
  assert.equal(f.toggle.hidden, false);
  await f.toggle.emit('click');
  assert.equal(f.menu.hidden, false);
});

for (const action of ['menuCopy', 'citationCopy']) {
  test(`${action} copies literal BibTeX and reports success beside its own control`, async () => {
    const f = fixture();
    assert.equal(f.menuCopy.hidden, false);
    assert.equal(f.citationCopy.hidden, false);
    await f.toggle.emit('click');
    await f[action].emit('click');
    assert.deepEqual(f.writes, [bibtex]);
    const ownStatus = action === 'menuCopy' ? f.shareStatus : f.citationStatus;
    const otherStatus = action === 'menuCopy' ? f.citationStatus : f.shareStatus;
    assert.equal(ownStatus.textContent, 'BibTeX copied to clipboard.');
    assert.equal(otherStatus.textContent, '');
    assert.equal(f[action].disabled, false);
    assert.equal(f.pre.focusCount, 0);
  });

  for (const clipboard of ['denied', 'unavailable']) {
    test(`${action} selects citation and keeps fallback visible when clipboard is ${clipboard}`, async () => {
      const f = fixture({ clipboard });
      await f.toggle.emit('click');
      await f[action].emit('click');
      assert.equal(f.selection.ranges.length, 1);
      assert.equal(f.selection.ranges[0].node, f.citation);
      assert.equal(f.pre.focusCount, 1);
      assert.equal(f.menu.hidden, true);
      assert.equal(f.shareStatus.textContent, '');
      assert.match(f.citationStatus.textContent, /citation is selected/);
      assert.equal(f[action].disabled, false);
    });
  }
}

test('copy actions disable only while their clipboard operation is pending', async () => {
  let finish;
  const f = fixture({ clipboard: () => new Promise(resolve => { finish = resolve; }) });
  const pending = f.menuCopy.emit('click');
  assert.equal(f.menuCopy.disabled, true);
  assert.equal(f.citationCopy.disabled, false);
  finish();
  await pending;
  assert.equal(f.menuCopy.disabled, false);
  assert.equal(f.shareStatus.textContent, 'BibTeX copied to clipboard.');
});
