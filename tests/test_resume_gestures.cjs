const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');
const vm = require('node:vm');

const script = fs.readFileSync(path.join(__dirname, '../static/assets/script/resume.js'), 'utf8');

// Small event/DOM fixture: run the shipped script, including its cloned lists,
// without a browser dependency. A prevented click stands in for blocked navigation.
class Element {
  constructor(tag = 'div', attributes = {}) {
    this.tag = tag;
    this.attributes = new Map(Object.entries(attributes));
    this.children = [];
    this.listeners = new Map();
    this.scrollLeft = 0;
    this.clientWidth = 240;
  }
  append(child) { child.parent = this; this.children.push(child); }
  remove() { this.parent.children = this.parent.children.filter(child => child !== this); }
  setAttribute(name, value) { this.attributes.set(name, value); }
  removeAttribute(name) { this.attributes.delete(name); }
  toggleAttribute(name, enabled) {
    if (enabled) this.setAttribute(name, '');
    else this.removeAttribute(name);
  }
  getBoundingClientRect() { return { width: 400 }; }
  matches(selector) {
    const match = /^(\w+)?(?:\.([\w-]+))?(?:\[([\w-]+)\])?$/.exec(selector);
    return !!match && (!match[1] || this.tag === match[1]) &&
      (!match[2] || (this.attributes.get('class') || '').split(' ').includes(match[2])) &&
      (!match[3] || this.attributes.has(match[3]));
  }
  querySelectorAll(selector) {
    return this.children.flatMap(child => [
      ...(child.matches(selector) ? [child] : []), ...child.querySelectorAll(selector),
    ]);
  }
  querySelector(selector) { return this.querySelectorAll(selector)[0] || null; }
  closest(selector) { return this.matches(selector) ? this : this.parent?.closest(selector); }
  contains(child) { return child === this || this.children.some(item => item.contains(child)); }
  cloneNode() {
    const copy = new Element(this.tag, Object.fromEntries(this.attributes));
    this.children.forEach(child => copy.append(child.cloneNode()));
    return copy;
  }
  addEventListener(type, callback, options) {
    const listeners = this.listeners.get(type) || [];
    listeners.push({ callback, capture: options === true || !!options?.capture });
    this.listeners.set(type, listeners);
  }
}

function fixture() {
  const document = new Element('document');
  const root = new Element('div', { 'data-badge-marquee': '' });
  const viewport = new Element('div', { class: 'resume__badges-viewport' });
  const track = new Element('div', { class: 'resume__badges-track' });
  const original = new Element('ul', { class: 'resume__summary-badges' });
  const item = new Element('li');
  const link = new Element('a', { class: 'resume__badge', href: 'https://example.org/award' });
  const label = new Element('span');
  document.append(root); root.append(viewport); viewport.append(track);
  track.append(original); original.append(item); item.append(link); link.append(label);
  original.append(new Element('li'));
  const window = new Element('window');
  let time = 0;
  Object.assign(window, {
    matchMedia: () => ({ matches: false, addEventListener() {} }),
    requestAnimationFrame: () => 1,
    cancelAnimationFrame() {},
    getComputedStyle: () => ({ columnGap: '8px' }),
    queueMicrotask,
  });
  vm.runInNewContext(script, {
    window, document, performance: { now: () => time },
    ResizeObserver: class { observe() {} },
  });

  function dispatch(type, target = label, properties = {}) {
    const event = {
      type, target, pointerId: 1, pointerType: 'mouse', isPrimary: true,
      button: 0, clientX: 20, clientY: 20, detail: 1,
      deltaX: 0, deltaY: 0, defaultPrevented: false,
      preventDefault() { this.defaultPrevented = true; }, ...properties,
    };
    const route = [];
    for (let node = target; node; node = node.parent) route.push(node);
    for (const capture of [true, false]) {
      const nodes = capture ? [...route].reverse() : route;
      for (const node of nodes) {
        for (const listener of node.listeners.get(type) || []) {
          if (listener.capture === capture) listener.callback(event);
        }
      }
    }
    return event;
  }
  function press(target = label, properties = {}) { dispatch('pointerdown', target, properties); }
  function release(target = label, properties = {}) { dispatch('pointerup', target, properties); }
  function click(target = label, properties = {}) { return dispatch('click', target, properties); }
  return { document, viewport, track, label, link, dispatch, press, release, click,
    elapse(ms) { time += ms; } };
}

test('ordinary mouse clicks and touch taps retain native link navigation', () => {
  for (const pointerType of ['mouse', 'touch', 'pen']) {
    const f = fixture();
    f.press(f.label, { pointerType }); f.elapse(100); f.release(f.label, { pointerType });
    assert.equal(f.click(f.label, { pointerType }).defaultPrevented, false);
  }
});

test('holding a badge suppresses activation, but a subsequent fresh click works', () => {
  const f = fixture();
  f.press(); f.elapse(500); f.release();
  assert.equal(f.click().defaultPrevented, true);
  f.press(); f.elapse(50); f.release();
  assert.equal(f.click().defaultPrevented, false);
});

test('ordinary middle clicks work while held or dragged middle clicks are cancelled', () => {
  for (const action of ['click', 'hold', 'drag']) {
    const f = fixture();
    f.press(f.label, { button: 1 });
    if (action === 'hold') f.elapse(500);
    if (action === 'drag') f.dispatch('pointermove', f.label, { button: 1, clientX: 35 });
    f.release(f.label, { button: 1 });
    assert.equal(f.dispatch('auxclick', f.label, { button: 1 }).defaultPrevented, action !== 'click', action);
  }
});

test('movement cancels activation even after returning to the starting point', () => {
  for (const pointerType of ['mouse', 'touch']) {
    const f = fixture();
    f.press(f.label, { pointerType });
    f.dispatch('pointermove', f.document, { pointerType, clientX: 28 });
    f.dispatch('pointermove', f.document, { pointerType, clientX: 20 });
    f.release(f.label, { pointerType });
    assert.equal(f.click(f.label, { pointerType }).defaultPrevented, true);
  }
});

test('minor pointer jitter still permits a click', () => {
  const f = fixture();
  f.press(); f.dispatch('pointermove', f.label, { clientX: 24, clientY: 24 }); f.release();
  assert.equal(f.click().defaultPrevented, false);
});

test('wheel gestures, viewport scrolling, and page scrolling cancel activation', () => {
  for (const kind of ['wheel', 'viewport', 'page']) {
    const f = fixture();
    f.press();
    if (kind === 'wheel') f.dispatch('wheel', f.label, { deltaY: 10 });
    else if (kind === 'viewport') {
      f.viewport.scrollLeft = 10; f.dispatch('scroll', f.viewport);
    } else f.dispatch('scroll', f.document);
    f.release();
    assert.equal(f.click().defaultPrevented, true, kind);
  }
});

test('a queued scroll event without new movement does not cancel a clean click', () => {
  const f = fixture();
  f.viewport.scrollLeft = 10;
  f.press(); f.dispatch('scroll', f.viewport); f.release();
  assert.equal(f.click().defaultPrevented, false);
});

test('scroll movement cancels activation even before the asynchronous scroll event arrives', () => {
  const f = fixture();
  f.press(); f.release();
  f.viewport.scrollLeft = 10;
  assert.equal(f.click().defaultPrevented, true);
});

test('pointer cancellation and context menus suppress synthetic follow-up clicks', () => {
  for (const event of ['pointercancel', 'contextmenu']) {
    const f = fixture();
    f.press(); f.dispatch(event); f.release();
    assert.equal(f.click().defaultPrevented, true, event);
  }
});

test('keyboard and assistive-technology activation survive a cancelled pointer gesture', () => {
  const f = fixture();
  f.press(); f.elapse(700); f.release();
  assert.equal(f.click(f.link, { detail: 0, pointerType: '' }).defaultPrevented, false);
});

test('repeated badges have the same click guards and no duplicate tab stops', () => {
  const f = fixture();
  const copies = f.track.querySelectorAll('[data-badge-copy]');
  assert.ok(copies.length > 0);
  copies.forEach(copy => {
    const link = copy.querySelector('a[href]');
    assert.equal(link.tabIndex, -1);
    f.press(link); f.release(link);
    assert.equal(f.click(link).defaultPrevented, false);
    f.press(link); f.elapse(600); f.release(link);
    assert.equal(f.click(link).defaultPrevented, true);
  });
});
