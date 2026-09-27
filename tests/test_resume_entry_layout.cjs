const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');
const vm = require('node:vm');

const script = fs.readFileSync(path.join(__dirname, '../static/assets/script/resume.js'), 'utf8');
const stackedClass = 'resume__entry-header--stacked';

class Element {
  constructor(rect = {}) {
    this.rect = rect;
    this.listeners = new Map();
    const classes = new Set();
    this.classList = {
      add: name => classes.add(name),
      remove: name => classes.delete(name),
      contains: name => classes.has(name),
      toggle(name, enabled) {
        if (enabled) classes.add(name);
        else classes.delete(name);
      },
    };
  }
  getBoundingClientRect() { return { ...this.rect }; }
  addEventListener(type, callback) {
    const callbacks = this.listeners.get(type) || [];
    callbacks.push(callback);
    this.listeners.set(type, callbacks);
  }
  dispatch(type) { (this.listeners.get(type) || []).forEach(callback => callback({ type })); }
}

function fixture({ entries = [{}], resizeObserver = true, fonts = true } = {}) {
  const window = new Element();
  const document = new Element();
  const headers = entries.map(options => {
    const header = new Element();
    const row = new Element();
    const heading = new Element(options.headingRect || { top: 100, bottom: 128 });
    const period = new Element(options.periodRect || { top: 104, bottom: 124 });
    row.querySelector = selector => selector === 'h3' ?
      (options.heading === false ? null : heading) :
      selector === '.resume__period' && options.period !== false ? period : null;
    header.querySelector = selector => selector === '.resume__entry-heading' &&
      options.row !== false ? row : null;
    return { header, row, heading, period };
  });
  document.querySelectorAll = selector => selector === '.resume__entry-header' ?
    headers.map(entry => entry.header) : [];

  const observers = [];
  class ResizeObserver {
    constructor(callback) { this.callback = callback; this.targets = new Set(); observers.push(this); }
    observe(target) { this.targets.add(target); }
    disconnect() { this.targets.clear(); }
  }
  const frames = new Map();
  let nextFrame = 0;
  Object.assign(window, {
    location: { hash: '' },
    matchMedia: () => Object.assign(new Element(), { matches: false }),
    requestAnimationFrame(callback) { frames.set(++nextFrame, callback); return nextFrame; },
    cancelAnimationFrame(id) { frames.delete(id); },
  });
  let resolveFonts;
  if (fonts) document.fonts = { ready: new Promise(resolve => { resolveFonts = resolve; }) };
  const context = { window, document };
  if (resizeObserver) {
    window.ResizeObserver = ResizeObserver;
    context.ResizeObserver = ResizeObserver;
  }
  vm.runInNewContext(script, context);
  function flush() {
    const callbacks = [...frames.values()];
    frames.clear();
    callbacks.forEach(callback => callback());
  }
  flush();
  return {
    headers, observers, window,
    stacked: index => headers[index].header.classList.contains(stackedClass),
    resize() {
      observers.forEach(observer => observer.callback(
        [...observer.targets].map(target => ({ target })), observer));
      if (!resizeObserver) window.dispatch('resize');
      flush();
    },
    async fontsReady() { resolveFonts(); await Promise.resolve(); flush(); },
  };
}

test('each entry joins its metadata only when its date occupies a second row', () => {
  const f = fixture({ entries: [
    { periodRect: { top: 104, bottom: 124 } },
    { periodRect: { top: 136, bottom: 156 } },
  ] });
  assert.equal(f.stacked(0), false);
  assert.equal(f.stacked(1), true);
});

test('a date beside a multiline heading keeps split metadata despite unequal top positions', () => {
  const f = fixture({ entries: [{
    headingRect: { top: 100, bottom: 158 },
    periodRect: { top: 132, bottom: 152 },
  }] });
  assert.equal(f.stacked(0), false);
  f.headers[0].period.rect = { top: 166, bottom: 186 };
  f.resize();
  assert.equal(f.stacked(0), true);
});

test('resizing switches metadata in both directions without affecting other entries', () => {
  const f = fixture({ entries: [{}, {}] });
  assert.equal(f.observers.length, 1);
  assert.deepEqual([...f.observers[0].targets], f.headers.map(entry => entry.row));
  f.headers[0].period.rect = { top: 136, bottom: 156 };
  f.resize();
  assert.equal(f.stacked(0), true);
  assert.equal(f.stacked(1), false);
  f.headers[0].period.rect = { top: 104, bottom: 124 };
  f.headers[1].period.rect = { top: 136, bottom: 156 };
  f.resize();
  assert.equal(f.stacked(0), false);
  assert.equal(f.stacked(1), true);
});

test('entries without a date or heading are left alone and do not prevent other entries updating', () => {
  const f = fixture({ entries: [
    { period: false }, { heading: false }, { row: false },
    { periodRect: { top: 136, bottom: 156 } },
  ] });
  assert.deepEqual(f.headers.map((_, index) => f.stacked(index)), [false, false, false, true]);
  assert.deepEqual([...f.observers[0].targets], [f.headers[3].row]);
});

test('font loading rechecks wrapping after text metrics change', async () => {
  const f = fixture();
  f.headers[0].period.rect = { top: 136, bottom: 156 };
  await f.fontsReady();
  assert.equal(f.stacked(0), true);
});

test('window resizing keeps metadata in sync when ResizeObserver and font events are unavailable', () => {
  const f = fixture({ resizeObserver: false, fonts: false });
  f.headers[0].period.rect = { top: 136, bottom: 156 };
  f.resize();
  assert.equal(f.stacked(0), true);
  f.headers[0].period.rect = { top: 104, bottom: 124 };
  f.resize();
  assert.equal(f.stacked(0), false);
});

test('pages without resume entries initialize without requiring observer or font APIs', () => {
  const f = fixture({ entries: [], resizeObserver: false, fonts: false });
  assert.equal(f.headers.length, 0);
  f.resize();
});
