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
  const classList = new Set();
  classList.remove = (...tokens) => tokens.forEach(token => classList.delete(token));
  return {
    hidden: true,
    disabled: false,
    textContent: '',
    focusCount: 0,
    classList,
    setAttribute(name, value) { attributes.set(name, value); },
    removeAttribute(name) { attributes.delete(name); },
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

function fixture({ hasCitation = true, clipboard = 'success', deferReady = false,
  resource = false, hasCitationStatus = true, hasResourceStatus = true, labeled = true } = {}) {
  const document = element();
  const share = element();
  const menu = element();
  const toggle = element();
  const citationStatus = element();
  const citationCopy = element();
  const citationLabel = element();
  const citationIcon = element();
  const citationSection = element();
  const resourceNav = element();
  const resourceWrapper = element();
  const resourceCopy = element();
  const resourceFallback = element();
  const resourceLabel = element();
  const resourceIcon = element();
  const resourceStatus = element();
  const pre = element();
  const citation = { textContent: ` \n${bibtex}\n `, parentElement: pre };
  const writes = [];
  const selection = {
    ranges: [],
    removeAllRanges() { this.ranges = []; },
    addRange(range) { this.ranges.push(range); },
  };
  const copies = [...(hasCitation ? [citationCopy] : []), ...(resource ? [resourceCopy] : [])];
  const timers = new Map();
  let time = 0;
  let nextTimer = 0;
  document.body = element();
  document.activeElement = document.body;
  citationStatus.classList.add('visually-hidden');
  resourceStatus.classList.add('visually-hidden');
  citationLabel.textContent = 'Copy BibTeX';
  citationCopy.querySelector = selector => ({ '[data-copy-label]': labeled ? citationLabel : null, i: citationIcon })[selector] || null;
  if (labeled) citationCopy.setAttribute('data-copy-feedback', 'BibTex Copied!');
  citationCopy.focus = options => {
    citationCopy.focusCount += 1;
    citationCopy.focusOptions = options;
    document.activeElement = citationCopy;
  };
  resourceLabel.textContent = 'Cite this paper';
  resourceFallback.hidden = false;
  resourceCopy.setAttribute('data-copy-feedback', 'BibTex Copied!');
  resourceWrapper.querySelector = selector => ({
    '[data-copy-label]': resourceLabel,
    '[data-copy-citation-fallback]': resourceFallback,
  })[selector] || null;
  resourceWrapper.closest = selector => selector === '.post__resources' ? resourceNav : null;
  resourceNav.querySelector = selector => selector === '[data-copy-status]' && hasResourceStatus ? resourceStatus : null;
  resourceCopy.closest = selector => selector === '[data-copy-resource]' ? resourceWrapper : null;
  resourceCopy.querySelector = selector => ({ '[data-copy-label]': resourceLabel, i: resourceIcon })[selector] || null;
  resourceCopy.focus = options => {
    resourceCopy.focusCount += 1;
    resourceCopy.focusOptions = options;
    document.activeElement = resourceCopy;
  };
  citationSection.querySelector = selector => selector === '[data-copy-status]' && hasCitationStatus ? citationStatus : null;
  menu.hidden = false; // Static links are usable before enhancement.
  share.querySelector = selector => ({
    '[data-share-toggle]': toggle,
    '.share-menu': menu,
  })[selector] || null;
  share.contains = target => [share, toggle, menu].includes(target);
  pre.focus = () => {
    pre.focusCount += 1;
    document.activeElement = pre;
    share.emit('focusout', { relatedTarget: pre });
  };
  document.readyState = deferReady ? 'loading' : 'complete';
  document.querySelector = selector => selector === '[data-copy-status]' ?
    (resource && hasResourceStatus ? resourceStatus : hasCitation && hasCitationStatus ? citationStatus : null) : null;
  document.querySelectorAll = selector => ({
    '[data-share]': [share],
    '[data-copy-citation]': copies,
  })[selector] || [];
  document.getElementById = id => hasCitation ? {
    'post-bibtex': citation, 'post-citation': citationSection,
  }[id] || null : null;
  document.createRange = () => ({ selectNodeContents(node) { this.node = node; } });
  const navigator = {};
  if (clipboard !== 'unavailable') {
    navigator.clipboard = { async writeText(value) {
      writes.push(value);
      if (typeof clipboard === 'function') await clipboard();
      if (clipboard === 'denied') throw new Error('Permission denied');
    } };
  }
  const context = { document, navigator, window: {
    getSelection: () => selection,
    setTimeout(callback, delay) { const id = ++nextTimer; timers.set(id, { callback, at: time + delay }); return id; },
    clearTimeout(id) { timers.delete(id); },
  } };
  vm.runInNewContext(shareScript, context);
  vm.runInNewContext(postScript, context);
  return { document, share, menu, toggle, citationStatus,
    citationCopy, citationLabel, pre, citation, copies, writes, selection, resourceCopy,
    resourceFallback, resourceLabel, resourceIcon, resourceStatus,
    timerCount: () => timers.size,
    advance(milliseconds) {
      time += milliseconds;
      [...timers].filter(([, timer]) => timer.at <= time).forEach(([id, timer]) => {
        timers.delete(id);
        timer.callback();
      });
    },
  };
}

for (const hasCitation of [false, true]) {
  test(`Share initializes without a status region with citation=${hasCitation}, including Escape and outside/focus dismissal`, async () => {
    const f = fixture({ hasCitation });
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
}

test('Share also initializes without a citation when loaded before DOMContentLoaded', async () => {
  const f = fixture({ hasCitation: false, deferReady: true });
  assert.equal(f.toggle.hidden, true);
  assert.equal(f.menu.hidden, false);
  await f.document.emit('DOMContentLoaded');
  assert.equal(f.toggle.hidden, false);
  await f.toggle.emit('click');
  assert.equal(f.menu.hidden, false);
});

test('Citation copies literal BibTeX with temporary in-button success and an unobtrusive live status', async () => {
  const f = fixture();
  assert.equal(f.citationCopy.hidden, false);
  await f.toggle.emit('click');
  const icon = f.citationCopy.querySelector('i');
  f.citationCopy.focus();
  await f.citationCopy.emit('click');
  assert.deepEqual(f.writes, [bibtex]);
  assert.equal(f.citationStatus.textContent, 'BibTex Copied!');
  assert.equal(f.citationStatus.classList.has('visually-hidden'), true);
  assert.equal(f.citationLabel.textContent, 'BibTex Copied!');
  assert.equal(f.citationCopy.disabled, false);
  assert.equal(f.citationCopy.querySelector('i'), icon);
  assert.equal(f.document.activeElement, f.citationCopy);
  assert.equal(f.pre.focusCount, 0);
  f.advance(3000);
  assert.equal(f.citationLabel.textContent, 'Copy BibTeX');
});

for (const clipboard of ['denied', 'unavailable']) {
  test(`Citation selects its code and keeps fallback visible when clipboard is ${clipboard}`, async () => {
    const f = fixture({ clipboard });
    await f.toggle.emit('click');
    await f.citationCopy.emit('click');
    assert.equal(f.selection.ranges.length, 1);
    assert.equal(f.selection.ranges[0].node, f.citation);
    assert.equal(f.pre.focusCount, 1);
    assert.equal(f.menu.hidden, true);
    assert.match(f.citationStatus.textContent, /citation is selected/);
    assert.equal(f.citationStatus.classList.has('visually-hidden'), false);
    assert.equal(f.citationLabel.textContent, 'Copy BibTeX');
    assert.equal(f.citationCopy.disabled, false);
  });
}

test('labeled copy actions expose busy state while preserving native focus and blocking duplicate requests', async () => {
  let finish;
  const f = fixture({ resource: true, clipboard: () => new Promise(resolve => { finish = resolve; }) });
  f.citationCopy.focus();
  const pending = f.citationCopy.emit('click');
  assert.equal(f.citationCopy.disabled, false);
  assert.equal(f.citationCopy.getAttribute('aria-disabled'), 'true');
  assert.equal(f.citationCopy.getAttribute('aria-busy'), 'true');
  assert.equal(f.document.activeElement, f.citationCopy);
  assert.equal(f.resourceCopy.disabled, false);
  assert.equal(f.resourceCopy.getAttribute('aria-busy'), undefined);
  await f.citationCopy.emit('click');
  assert.equal(f.writes.length, 1);
  finish();
  await pending;
  assert.equal(f.citationCopy.disabled, false);
  assert.equal(f.citationCopy.getAttribute('aria-disabled'), undefined);
  assert.equal(f.citationCopy.getAttribute('aria-busy'), undefined);
  assert.equal(f.citationStatus.textContent, 'BibTex Copied!');
});

test('resource Cite progressively replaces its fallback and copies literal BibTeX with temporary feedback', async () => {
  const f = fixture({ resource: true });
  assert.equal(f.resourceCopy.hidden, false);
  assert.equal(f.resourceFallback.hidden, true);
  assert.equal(f.resourceLabel.textContent, 'Cite this paper');
  const icon = f.resourceCopy.querySelector('i');
  f.resourceCopy.focus();
  await f.resourceCopy.emit('click');
  assert.deepEqual(f.writes, [bibtex]);
  assert.equal(f.resourceLabel.textContent, 'BibTex Copied!');
  assert.equal(f.resourceStatus.textContent, 'BibTex Copied!');
  assert.equal(f.resourceStatus.classList.has('visually-hidden'), true);
  assert.equal(f.citationStatus.textContent, '');
  assert.equal(f.resourceCopy.querySelector('i'), icon);
  assert.equal(f.document.activeElement, f.resourceCopy);
  assert.equal(f.pre.focusCount, 0);
  f.advance(2999);
  assert.equal(f.resourceLabel.textContent, 'BibTex Copied!');
  f.advance(1);
  assert.equal(f.resourceLabel.textContent, 'Cite this paper');
  assert.equal(f.timerCount(), 0);
});

for (const clipboard of ['denied', 'unavailable']) {
  test(`resource Cite selects the citation on ${clipboard} clipboard without success feedback`, async () => {
    const f = fixture({ resource: true, clipboard });
    await f.resourceCopy.emit('click');
    assert.equal(f.selection.ranges.length, 1);
    assert.equal(f.selection.ranges[0].node, f.citation);
    assert.equal(f.pre.focusCount, 1);
    assert.equal(f.resourceLabel.textContent, 'Cite this paper');
    assert.equal(f.resourceStatus.textContent, '');
    assert.match(f.citationStatus.textContent, /citation is selected/);
    assert.equal(f.citationStatus.classList.has('visually-hidden'), false);
    assert.equal(f.resourceCopy.disabled, false);
    assert.equal(f.timerCount(), 0);
  });
}

test('resource copy retries reset feedback and ignore duplicate in-flight clicks', async () => {
  let finish;
  let attempt = 0;
  const f = fixture({ resource: true, clipboard: () => {
    attempt += 1;
    return attempt === 1 ? Promise.resolve() : new Promise((resolve, reject) => { finish = reject; });
  } });
  await f.resourceCopy.emit('click');
  assert.equal(f.timerCount(), 1);
  const pending = f.resourceCopy.emit('click');
  assert.equal(f.resourceCopy.disabled, false, 'The resource button keeps native keyboard focus');
  assert.equal(f.resourceCopy.getAttribute('aria-disabled'), 'true');
  assert.equal(f.resourceCopy.getAttribute('aria-busy'), 'true');
  assert.equal(f.resourceLabel.textContent, 'Cite this paper');
  assert.equal(f.timerCount(), 0);
  await f.resourceCopy.emit('click');
  assert.equal(f.writes.length, 2);
  finish(new Error('Permission denied'));
  await pending;
  assert.equal(f.resourceCopy.disabled, false);
  assert.equal(f.resourceCopy.getAttribute('aria-disabled'), undefined);
  assert.equal(f.resourceCopy.getAttribute('aria-busy'), undefined);
  assert.equal(f.resourceLabel.textContent, 'Cite this paper');
  assert.equal(f.resourceStatus.textContent, '');
  assert.match(f.citationStatus.textContent, /citation is selected/);
  f.advance(3000);
  assert.equal(f.resourceLabel.textContent, 'Cite this paper');
});

test('successful copy restores departed focus without taking focus from another control', async () => {
  for (const moveAway of [false, true]) {
    let finish;
    const f = fixture({ resource: true, clipboard: () => new Promise(resolve => { finish = resolve; }) });
    f.resourceCopy.focus();
    const pending = f.resourceCopy.emit('click');
    const target = moveAway ? f.toggle : f.document.body;
    f.document.activeElement = target;
    finish();
    await pending;
    assert.equal(f.document.activeElement, moveAway ? f.toggle : f.resourceCopy);
    if (!moveAway) assert.equal(f.resourceCopy.focusOptions.preventScroll, true);
  }
});

test('Citation and resource actions report feedback only in their own status region', async () => {
  const f = fixture({ resource: true });
  await f.citationCopy.emit('click');
  assert.equal(f.citationStatus.textContent, 'BibTex Copied!');
  assert.equal(f.resourceStatus.textContent, '');
  await f.resourceCopy.emit('click');
  assert.equal(f.resourceStatus.textContent, 'BibTex Copied!');
  assert.equal(f.citationStatus.textContent, '');
});

test('retrying any labeled copy control hides the visible manual-copy message before reporting success', async () => {
  for (const action of ['citationCopy', 'resourceCopy']) {
    let finish;
    let attempt = 0;
    const f = fixture({ resource: true, clipboard: () => {
      if (++attempt === 1) throw new Error('Permission denied');
      return new Promise(resolve => { finish = resolve; });
    } });
    await f[action].emit('click');
    assert.equal(f.citationStatus.classList.has('visually-hidden'), false);
    assert.match(f.citationStatus.textContent, /citation is selected/);
    const pending = f[action].emit('click');
    assert.equal(f.citationStatus.classList.has('visually-hidden'), true);
    assert.equal(f.citationStatus.textContent, '');
    finish();
    await pending;
    const ownStatus = action === 'citationCopy' ? f.citationStatus : f.resourceStatus;
    assert.equal(ownStatus.textContent, 'BibTex Copied!');
    assert.equal(ownStatus.classList.has('visually-hidden'), true);
  }
});

test('unlabeled Citation controls retain a visible success status', async () => {
  const f = fixture({ labeled: false });
  await f.citationCopy.emit('click');
  assert.equal(f.citationStatus.textContent, 'BibTeX copied to clipboard.');
  assert.equal(f.citationStatus.classList.has('visually-hidden'), false);
  assert.equal(f.timerCount(), 0);
});

test('manual-copy fallback is visible in the control status when the citation section status is unavailable', async () => {
  const f = fixture({ resource: true, hasCitationStatus: false, clipboard: 'denied' });
  await f.resourceCopy.emit('click');
  assert.equal(f.resourceStatus.classList.has('visually-hidden'), false);
  assert.match(f.resourceStatus.textContent, /citation is selected/);
  assert.equal(f.resourceLabel.textContent, 'Cite this paper');
  assert.equal(f.pre.focusCount, 1);
});

test('incomplete resource enhancement keeps its fallback link usable', () => {
  for (const options of [{ hasCitation: false }, { hasCitationStatus: false, hasResourceStatus: false }]) {
    const f = fixture({ resource: true, ...options });
    assert.equal(f.resourceCopy.hidden, true);
    assert.equal(f.resourceFallback.hidden, false);
    assert.equal(f.timerCount(), 0);
  }
});
