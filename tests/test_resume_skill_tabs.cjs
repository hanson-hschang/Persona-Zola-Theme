const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');
const vm = require('node:vm');

const script = fs.readFileSync(path.join(__dirname, '../static/assets/script/resume.js'), 'utf8');

// Exercise the shipped event handlers with unequal tab widths and asynchronous
// scroll/frame delivery. Browser rendering remains covered by the preview check.
class Element {
  constructor(attributes = {}) {
    this.attributes = new Map(Object.entries(attributes));
    this.listeners = new Map();
    this.hiddenWrites = 0;
    const properties = new Map();
    this.style = {
      setProperty(name, value) { properties.set(name, String(value)); },
      getPropertyValue(name) { return properties.get(name) || ''; },
    };
  }
  get id() { return this.attributes.get('id'); }
  getAttribute(name) { return this.attributes.get(name); }
  setAttribute(name, value) { this.attributes.set(name, value); }
  toggleAttribute(name, force = !this.attributes.has(name)) {
    if (force) this.attributes.set(name, '');
    else this.attributes.delete(name);
    return force;
  }
  set hidden(value) { this.isHidden = value; this.hiddenWrites += 1; }
  get hidden() { return this.isHidden; }
  addEventListener(type, callback) {
    const listeners = this.listeners.get(type) || [];
    listeners.push(callback);
    this.listeners.set(type, listeners);
  }
  dispatch(type, properties = {}) {
    const event = { type, target: this, defaultPrevented: false,
      preventDefault() { this.defaultPrevented = true; }, ...properties };
    (this.listeners.get(type) || []).forEach(callback => callback(event));
    return event;
  }
}

function fixture({ width = 320, mobile = true, widths = [220, 280, 210, 340], hash = '',
  cornerWidth = 9, observeResize = false, fontLoading = false } = {}) {
  const window = new Element();
  const document = new Element();
  const root = new Element();
  const rail = new Element();
  const narrowScreen = new Element();
  narrowScreen.matches = mobile;
  rail.clientWidth = width;
  rail.scrollWidth = widths.reduce((sum, value) => sum + value, 0) + (widths.length - 1) * 8;
  let scrollLeft = 0;
  Object.defineProperty(rail, 'scrollLeft', {
    get: () => scrollLeft,
    set: value => { scrollLeft = Math.max(0, Math.min(value, rail.scrollWidth - rail.clientWidth)); },
  });
  rail.getBoundingClientRect = () => ({ left: 24, right: 24 + rail.clientWidth });
  const panels = widths.map((_, index) => new Element({ id: 'panel-' + index }));
  let offset = 0;
  const tabs = widths.map((tabWidth, index) => {
    const tab = new Element({ href: '#panel-' + index });
    const left = offset;
    offset += tabWidth + 8;
    tab.getBoundingClientRect = () => ({ left: 24 + left - scrollLeft,
      right: 24 + left + tabWidth - scrollLeft });
    tab.focus = () => { document.activeElement = tab; tab.dispatch('focus'); };
    return tab;
  });
  root.querySelector = selector => selector === '.resume__skill-tabs' ? rail :
    panels.find(panel => '#' + panel.id === selector);
  root.querySelectorAll = selector => selector === '.resume__skill-tab' ? tabs : [];
  document.querySelectorAll = selector => selector === '[data-skill-tabs]' ? [root] : [];
  let finishFonts;
  if (fontLoading) document.fonts = { ready: new Promise(resolve => { finishFonts = resolve; }) };
  const observers = [];
  class ResizeObserver {
    constructor(callback) { this.callback = callback; this.targets = []; observers.push(this); }
    observe(target) { this.targets.push(target); }
  }
  const frames = new Map();
  let nextFrame = 0;
  Object.assign(window, {
    location: { hash },
    matchMedia: query => query === '(max-width: 767px)' ? narrowScreen : new Element(),
    getComputedStyle: () => ({ width: cornerWidth + 'px' }),
    requestAnimationFrame(callback) { frames.set(++nextFrame, callback); return nextFrame; },
    cancelAnimationFrame(id) { frames.delete(id); },
  });
  if (observeResize) window.ResizeObserver = ResizeObserver;
  vm.runInNewContext(script, { window, document, ...(observeResize ? { ResizeObserver } : {}) });
  function flush() {
    const callbacks = [...frames.values()];
    frames.clear();
    callbacks.forEach(callback => callback());
  }
  function scroll(position, wait = true) {
    rail.scrollLeft = position;
    rail.dispatch('scroll');
    if (wait) flush();
  }
  return { window, document, root, rail, tabs, panels, frames, flush, scroll, observers, finishFonts,
    selected: () => tabs.findIndex(tab => tab.getAttribute('aria-selected') === 'true'),
    clipped: () => ({ left: root.attributes.has('data-skill-clipped-left'),
      right: root.attributes.has('data-skill-clipped-right') }),
    resize(nextWidth, nextMobile) {
      rail.clientWidth = nextWidth;
      rail.scrollLeft = rail.scrollLeft;
      if (narrowScreen.matches !== nextMobile) {
        narrowScreen.matches = nextMobile;
        narrowScreen.dispatch('change');
      }
      window.dispatch('resize');
      rail.dispatch('scroll');
      flush();
    },
  };
}

test('small-screen scrolling shows the category nearest the visible center without moving the rail', () => {
  const f = fixture();
  assert.equal(f.selected(), 0);
  f.scroll(200);
  assert.equal(f.selected(), 1);
  assert.equal(f.rail.scrollLeft, 200);
  f.scroll(470);
  assert.equal(f.selected(), 2);
  assert.equal(f.rail.scrollLeft, 470);
  assert.deepEqual(f.panels.map(panel => panel.hidden), [true, true, false, true]);
  assert.deepEqual(f.tabs.map(tab => tab.tabIndex), [-1, -1, 0, -1]);
  assert.equal(f.document.activeElement, undefined);
});

test('the first and last category remain selectable at the ends even when their tabs are narrow', () => {
  const f = fixture({ widths: [50, 70, 400, 60] });
  f.scroll(100);
  assert.equal(f.selected(), 2);
  f.scroll(0);
  assert.equal(f.selected(), 0);
  f.scroll(f.rail.scrollWidth - f.rail.clientWidth);
  assert.equal(f.selected(), 3);
});

test('scrolling back and repeated events preserve panel animation and batch DOM updates', () => {
  const f = fixture();
  f.scroll(470);
  const writes = f.panels.map(panel => panel.hiddenWrites);
  f.scroll(480, false);
  f.scroll(490, false);
  assert.equal(f.frames.size, 1);
  f.flush();
  assert.deepEqual(f.panels.map(panel => panel.hiddenWrites), writes);
  f.scroll(200);
  assert.equal(f.selected(), 1);
});

test('desktop scrolling preserves its category while mouse hover and click still select tabs', () => {
  const f = fixture({ mobile: false });
  f.scroll(470);
  assert.equal(f.selected(), 0);
  f.tabs[2].dispatch('pointerenter', { pointerType: 'mouse' });
  assert.equal(f.selected(), 2);
  assert.equal(f.tabs[1].dispatch('click').defaultPrevented, true);
  f.rail.dispatch('scroll'); f.flush();
  assert.equal(f.selected(), 1);
});

test('click selection wins over a queued scroll and its asynchronous reveal event', () => {
  const f = fixture({ widths: [50, 70, 400, 60] });
  f.scroll(100, false);
  f.tabs[0].dispatch('click');
  f.rail.dispatch('scroll'); f.flush();
  assert.equal(f.selected(), 0);
  assert.equal(f.rail.scrollLeft, 0);
  f.scroll(8);
  assert.equal(f.selected(), 1);
});

test('keyboard navigation and focus remain authoritative on small screens', () => {
  const f = fixture({ widths: [50, 70, 400, 60] });
  f.scroll(100, false);
  assert.equal(f.tabs[0].dispatch('keydown', { key: 'End' }).defaultPrevented, true);
  f.rail.dispatch('scroll'); f.flush();
  assert.equal(f.selected(), 3);
  assert.equal(f.document.activeElement, f.tabs[3]);
  f.tabs[3].dispatch('keydown', { key: 'Home' });
  f.rail.dispatch('scroll'); f.flush();
  assert.equal(f.selected(), 0);
  assert.equal(f.document.activeElement, f.tabs[0]);
  f.tabs[0].dispatch('keydown', { key: 'ArrowRight' });
  assert.equal(f.selected(), 1);
  f.tabs[1].dispatch('keydown', { key: 'ArrowLeft' });
  assert.equal(f.selected(), 0);
  f.tabs[0].dispatch('keydown', { key: ' ' });
  f.rail.dispatch('scroll'); f.flush();
  assert.equal(f.selected(), 0);
});

test('resizing preserves the chosen tab and allows the next mobile scroll to select normally', () => {
  const f = fixture({ width: 1280, mobile: false });
  f.tabs[2].dispatch('click');
  f.resize(320, true);
  assert.equal(f.selected(), 2);
  f.scroll(200);
  assert.equal(f.selected(), 1);
  f.resize(1000, false);
  assert.equal(f.selected(), 1);
  f.scroll(50);
  assert.equal(f.selected(), 1);
});

test('wheel scrolling updates mobile panels and ignores browser zoom gestures', () => {
  const f = fixture();
  const event = f.rail.dispatch('wheel', { deltaX: 0, deltaY: 200, deltaMode: 0 });
  assert.equal(event.defaultPrevented, true);
  f.rail.dispatch('scroll'); f.flush();
  assert.equal(f.selected(), 1);
  f.rail.dispatch('wheel', { ctrlKey: true, deltaY: 200, deltaMode: 0 });
  assert.equal(f.rail.scrollLeft, 200);
});

test('nonoverflowing rails and deep-linked panels retain their selected category', () => {
  const f = fixture({ widths: [50, 70], hash: '#panel-1' });
  assert.equal(f.selected(), 1);
  f.scroll(0);
  assert.equal(f.selected(), 1);
});

test('desktop scrolling squares only the panel corner under the clipped selected tab', () => {
  const f = fixture({ width: 250, mobile: false, widths: [100, 200, 100], hash: '#panel-1' });
  assert.deepEqual(f.clipped(), { left: false, right: true });
  f.scroll(100);
  assert.equal(f.selected(), 1);
  assert.deepEqual(f.clipped(), { left: false, right: false });
  f.scroll(110);
  assert.equal(f.selected(), 1);
  assert.deepEqual(f.clipped(), { left: true, right: false });
});

test('a selected tab wider than the rail can square both panel corners', () => {
  const f = fixture({ width: 250, mobile: false, widths: [100, 400, 100], hash: '#panel-1' });
  f.scroll(160);
  assert.deepEqual(f.clipped(), { left: true, right: true });
});

test('the flared tab corners count as clipped with a one-pixel tolerance', () => {
  const f = fixture({ width: 250, mobile: false, widths: [100, 200, 100], hash: '#panel-1' });
  f.scroll(101);
  assert.deepEqual(f.clipped(), { left: false, right: false });
  f.scroll(102);
  assert.deepEqual(f.clipped(), { left: true, right: false });
  f.scroll(64);
  assert.deepEqual(f.clipped(), { left: false, right: true });
  f.scroll(65);
  assert.deepEqual(f.clipped(), { left: false, right: false });

  const withoutFlare = fixture({ width: 250, mobile: false, widths: [100, 200, 100],
    hash: '#panel-1', cornerWidth: 0 });
  withoutFlare.scroll(102);
  assert.deepEqual(withoutFlare.clipped(), { left: false, right: false });
});

test('selecting another category clears clipping left over from the previous tab', () => {
  const f = fixture({ width: 250, mobile: false, widths: [100, 200, 100], hash: '#panel-1' });
  assert.deepEqual(f.clipped(), { left: false, right: true });
  f.tabs[0].dispatch('pointerenter', { pointerType: 'mouse' });
  assert.equal(f.selected(), 0);
  assert.deepEqual(f.clipped(), { left: true, right: false });
  f.tabs[1].dispatch('click');
  assert.equal(f.selected(), 1);
  assert.equal(f.rail.scrollLeft, 58);
  assert.deepEqual(f.clipped(), { left: false, right: true });
  f.rail.dispatch('scroll'); f.flush();
  assert.deepEqual(f.clipped(), { left: false, right: true });
});

test('mobile scrolling refreshes clipping without restarting the selected panel', () => {
  const f = fixture({ width: 250, widths: [100, 200, 100], hash: '#panel-1' });
  f.scroll(64);
  const writes = f.panels.map(panel => panel.hiddenWrites);
  assert.deepEqual(f.clipped(), { left: false, right: true });
  f.scroll(100);
  assert.equal(f.selected(), 1);
  assert.deepEqual(f.clipped(), { left: false, right: false });
  assert.deepEqual(f.panels.map(panel => panel.hiddenWrites), writes);
});

test('resizing restores rounded panel corners when the selected tab fits again', () => {
  const f = fixture({ width: 250, mobile: false, widths: [100, 400, 100], hash: '#panel-1' });
  f.scroll(160);
  assert.deepEqual(f.clipped(), { left: true, right: true });
  f.resize(620, false);
  assert.equal(f.selected(), 1);
  assert.deepEqual(f.clipped(), { left: false, right: false });
  f.resize(250, false);
  assert.equal(f.selected(), 1);
  assert.deepEqual(f.clipped(), { left: true, right: true });
});

test('desktop clipping updates share one frame for repeated scroll events', () => {
  const f = fixture({ width: 250, mobile: false, widths: [100, 200, 100], hash: '#panel-1' });
  const writes = f.panels.map(panel => panel.hiddenWrites);
  f.scroll(100, false);
  f.scroll(110, false);
  assert.equal(f.frames.size, 1);
  assert.deepEqual(f.clipped(), { left: false, right: true });
  f.flush();
  assert.deepEqual(f.clipped(), { left: true, right: false });
  assert.deepEqual(f.panels.map(panel => panel.hiddenWrites), writes);
});

test('container and tab size changes refresh clipping without a window resize', () => {
  const f = fixture({ width: 250, mobile: false, widths: [100, 200, 100], hash: '#panel-1',
    observeResize: true });
  const observer = f.observers.find(item => item.targets.includes(f.rail));
  assert.ok(observer);
  assert.ok(observer.targets.includes(f.tabs[1]));
  assert.deepEqual(f.clipped(), { left: false, right: true });
  f.rail.clientWidth = 420;
  observer.callback();
  assert.deepEqual(f.clipped(), { left: false, right: false });
  f.tabs[1].getBoundingClientRect = () => ({ left: 20, right: 450 });
  observer.callback();
  assert.deepEqual(f.clipped(), { left: true, right: true });
  assert.equal(f.selected(), 1);
  assert.equal(f.rail.scrollLeft, 0);
});

test('loaded fonts refresh the selected tab clipping', async () => {
  const f = fixture({ width: 400, mobile: false, widths: [100, 200, 100], hash: '#panel-1',
    fontLoading: true });
  assert.deepEqual(f.clipped(), { left: false, right: false });
  f.tabs[1].getBoundingClientRect = () => ({ left: 132, right: 450 });
  f.finishFonts();
  await f.document.fonts.ready;
  assert.equal(f.selected(), 1);
  assert.deepEqual(f.clipped(), { left: false, right: true });
});

test('scrolling opens either rail edge independently of the active tab', () => {
  const f = fixture({ width: 250, mobile: false, widths: [100, 200, 100], hash: '#panel-1' });
  const openEdges = () => ({
    left: f.root.attributes.has('data-skill-scroll-left'),
    right: f.root.attributes.has('data-skill-scroll-right'),
  });
  assert.deepEqual(openEdges(), { left: false, right: true });
  f.scroll(100);
  assert.deepEqual(openEdges(), { left: true, right: true });
  assert.deepEqual(f.clipped(), { left: false, right: false });
  assert.equal(f.selected(), 1);
  assert.equal(f.rail.scrollLeft, 100);
  assert.equal(f.rail.clientWidth, 250);
  f.scroll(f.rail.scrollWidth - f.rail.clientWidth);
  assert.deepEqual(openEdges(), { left: true, right: false });
  f.scroll(0);
  assert.deepEqual(openEdges(), { left: false, right: true });
  f.resize(500, false);
  assert.deepEqual(openEdges(), { left: false, right: false });
});

test('moving corner offsets preserve fractional scrolling at both ends without changing selection', () => {
  const f = fixture({ width: 250, mobile: false, widths: [100, 200, 100], hash: '#panel-1' });
  const limit = f.rail.scrollWidth - f.rail.clientWidth;
  const writes = f.panels.map(panel => panel.hiddenWrites);
  const positions = [0, 0.25, 0.75, 1.25, 8.5, limit - 8.5,
    limit - 1.25, limit - 0.75, limit - 0.25, limit];
  for (const position of [...positions, ...positions.slice().reverse()]) {
    f.scroll(position);
    assert.equal(f.root.style.getPropertyValue('--resume-tabs-scroll-left'), position + 'px');
    assert.equal(f.root.style.getPropertyValue('--resume-tabs-scroll-right'), (limit - position) + 'px');
    assert.equal(f.rail.scrollLeft, position);
    assert.equal(f.selected(), 1);
  }
  assert.deepEqual(f.panels.map(panel => panel.hiddenWrites), writes);
});

test('nonoverflowing rails reset moving corner offsets to zero', () => {
  const f = fixture({ width: 250, mobile: false, widths: [100, 200, 100], hash: '#panel-1' });
  f.scroll(8.5);
  f.resize(500, false);
  assert.equal(f.root.style.getPropertyValue('--resume-tabs-scroll-left'), '0px');
  assert.equal(f.root.style.getPropertyValue('--resume-tabs-scroll-right'), '0px');
  assert.equal(f.selected(), 1);

  const fitted = fixture({ widths: [50, 70], hash: '#panel-1' });
  assert.equal(fitted.root.style.getPropertyValue('--resume-tabs-scroll-left'), '0px');
  assert.equal(fitted.root.style.getPropertyValue('--resume-tabs-scroll-right'), '0px');
  assert.equal(fitted.selected(), 1);
});
