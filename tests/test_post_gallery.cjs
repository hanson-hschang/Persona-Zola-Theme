const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');
const vm = require('node:vm');

const script = fs.readFileSync(path.join(__dirname, '../static/assets/script/post-gallery.js'), 'utf8');

function fixture({ collections = [[['Research'], ['Travel'], []]], observers = true,
  run = true, row = 1, padding = 24, gap = 0, mediaGallery = false } = {}) {
  const frames = new Map();
  const windowListeners = new Map();
  const fontCallbacks = [];
  const observed = [];
  let nextFrame = 0;
  const document = { activeElement: null, fonts: { ready: { then: callback => fontCallbacks.push(callback) } } };

  class Element {
    constructor(type, data = {}) {
      this.type = type;
      this.dataset = data;
      this.hidden = false;
      this.attributes = new Map();
      this.listeners = new Map();
      this.children = [];
      this.style = {};
      this.height = 100;
    }
    append(element) { element.parent = this; this.children.push(element); return element; }
    querySelectorAll(selector) {
      const accepted = {
        '[data-post-grid]': 'grid', '[data-post-filters]': 'filters', '.post-card': 'card',
        '.post-card__link': 'link', 'button[data-post-filter]': 'button', img: 'image',
      };
      assert.ok(Object.hasOwn(accepted, selector), `unexpected selector ${selector}`);
      const descendants = this.children.flatMap(child => [child, ...child.descendants()]);
      return descendants.filter(element => element.type === accepted[selector]);
    }
    descendants() { return this.children.flatMap(child => [child, ...child.descendants()]); }
    querySelector(selector) { return this.querySelectorAll(selector)[0] || null; }
    setAttribute(name, value) { this.attributes.set(name, value); }
    removeAttribute(name) { this.attributes.delete(name); }
    getAttribute(name) { return this.attributes.get(name) ?? null; }
    hasAttribute(name) { return this.attributes.has(name); }
    addEventListener(type, callback) {
      const callbacks = this.listeners.get(type) || [];
      callbacks.push(callback);
      this.listeners.set(type, callbacks);
    }
    contains(element) { return this === element || this.descendants().includes(element); }
    getBoundingClientRect() { return { height: this.height }; }
    focus(options) { document.activeElement = this; this.focusOptions = options; }
    emit(type) { (this.listeners.get(type) || []).forEach(callback => callback({ target: this })); }
  }

  const galleries = collections.map(collection => {
    const gallery = new Element('gallery');
    const filters = gallery.append(new Element('filters'));
    filters.hidden = true;
    const grid = gallery.append(new Element('grid'));
    const categories = new Set(collection.flatMap(value => Array.isArray(value) ? value : []));
    const buttons = ['', ...categories].map(category =>
      filters.append(new Element('button', { postFilter: category })));
    const cards = collection.map((value, index) => {
      const card = grid.append(new Element('card', {
        postCategories: Array.isArray(value) ? JSON.stringify(value) : value,
      }));
      const link = card.append(new Element('link'));
      link.height = 100 + index * 55;
      link.append(new Element('image'));
      return card;
    });
    return { gallery, filters, grid, buttons, cards };
  });
  document.querySelectorAll = selector => {
    assert.equal(selector, '[data-post-gallery]');
    return [...galleries.map(({ gallery }) => gallery), ...(mediaGallery ? [new Element('gallery')] : [])];
  };
  const window = {
    requestAnimationFrame(callback) { const id = ++nextFrame; frames.set(id, callback); return id; },
    addEventListener(type, callback) {
      const callbacks = windowListeners.get(type) || [];
      callbacks.push(callback);
      windowListeners.set(type, callbacks);
    },
    getComputedStyle(element) {
      if (element.type === 'grid') {
        return { gridAutoRows: element.hasAttribute('data-post-masonry-ready') ? `${row}px` : 'auto', rowGap: `${gap}px` };
      }
      return { paddingBottom: element.parent.hasAttribute('data-post-masonry-ready') ? `${padding}px` : '0px' };
    },
  };
  if (observers) {
    window.ResizeObserver = class {
      constructor(callback) { this.callback = callback; }
      observe(element) { observed.push({ element, callback: this.callback }); }
    };
  }
  const execute = () => vm.runInNewContext(script, { document, window });
  if (run) execute();
  return {
    galleries, document, observed, run: execute,
    pending: () => frames.size,
    flush() {
      for (let count = 0; frames.size; count += 1) {
        assert.ok(count < 10, 'layout must settle');
        const batch = [...frames.values()];
        frames.clear();
        batch.forEach(callback => callback());
      }
    },
    event(type) { (windowListeners.get(type) || []).forEach(callback => callback()); },
    fontsReady() { fontCallbacks.forEach(callback => callback()); },
    resizeObserved(element) { observed.filter(item => item.element === element).forEach(item => item.callback()); },
  };
}

test('all cards are readable before enhancement; ready native buttons expose their active state', () => {
  const f = fixture({ run: false });
  const { filters, buttons, cards } = f.galleries[0];
  assert.equal(filters.hidden, true);
  assert.ok(cards.every(card => !card.hidden));
  f.run();
  assert.equal(filters.hidden, false);
  assert.deepEqual(buttons.map(button => button.getAttribute('aria-pressed')), ['true', 'false', 'false']);
  buttons[1].focus();
  buttons[1].emit('click');
  assert.deepEqual(cards.map(card => card.hidden), [false, true, true]);
  assert.equal(f.document.activeElement, buttons[1]);
  assert.deepEqual(buttons.map(button => button.getAttribute('aria-pressed')), ['false', 'true', 'false']);
  buttons[0].emit('click');
  assert.ok(cards.every(card => !card.hidden));
});

test('category matching is exact, supports multiple labels and selector characters, and stays within its gallery', () => {
  const special = 'Control ["soft"] / & Dynamics';
  const f = fixture({ collections: [[['Research', special], ['research'], ['Research notes']], [['Travel'], ['Research']]] });
  const first = f.galleries[0];
  first.buttons.find(button => button.dataset.postFilter === 'Research').emit('click');
  assert.deepEqual(first.cards.map(card => card.hidden), [false, true, true]);
  assert.ok(f.galleries[1].cards.every(card => !card.hidden));
  assert.equal(f.galleries[1].buttons[0].getAttribute('aria-pressed'), 'true');
  first.buttons.find(button => button.dataset.postFilter === special).emit('click');
  assert.deepEqual(first.cards.map(card => card.hidden), [false, true, true]);
});

test('malformed category data does not break initialization or the All filter', () => {
  const f = fixture({ collections: [['invalid JSON', '{"category":"Research"}', ['Research']]] });
  const { buttons, cards } = f.galleries[0];
  assert.ok(cards.every(card => !card.hidden));
  buttons[1].emit('click');
  assert.deepEqual(cards.map(card => card.hidden), [true, true, false]);
  buttons[0].emit('click');
  assert.ok(cards.every(card => !card.hidden));
});

test('filtering a focused card restores focus to the chosen native button without reordering cards', () => {
  const f = fixture();
  const { buttons, cards, grid } = f.galleries[0];
  const order = [...grid.children];
  cards[1].querySelector('.post-card__link').focus();
  buttons[1].emit('click');
  assert.equal(f.document.activeElement, buttons[1]);
  assert.equal(buttons[1].focusOptions.preventScroll, true);
  f.flush();
  assert.deepEqual(grid.children, order);
});

test('masonry uses each natural height and configured spacing; filtering removes hidden card spans', () => {
  const f = fixture({ row: 2, padding: 32, gap: 0 });
  const { cards, grid, buttons } = f.galleries[0];
  f.flush();
  assert.equal(grid.hasAttribute('data-post-masonry-ready'), true);
  assert.deepEqual(cards.map(card => card.style.gridRowEnd), ['span 66', 'span 94', 'span 121']);
  buttons[1].emit('click');
  f.flush();
  assert.deepEqual(cards.map(card => card.style.gridRowEnd), ['span 66', '', '']);
  buttons[0].emit('click');
  f.flush();
  assert.deepEqual(cards.map(card => card.style.gridRowEnd), ['span 66', 'span 94', 'span 121']);
});

test('resize observers, late images, and loaded fonts refresh heights in one scheduled frame', () => {
  const f = fixture();
  const { cards, grid } = f.galleries[0];
  const link = cards[0].querySelector('.post-card__link');
  f.flush();
  assert.equal(cards[0].style.gridRowEnd, 'span 124');
  assert.ok(f.observed.some(item => item.element === grid));
  assert.ok(f.observed.some(item => item.element === link));
  link.height = 188;
  f.resizeObserved(link);
  f.resizeObserved(grid);
  link.querySelector('img').emit('load');
  f.fontsReady();
  assert.equal(f.pending(), 1);
  f.flush();
  assert.equal(cards[0].style.gridRowEnd, 'span 212');
});

test('responsive layout works without ResizeObserver and falls back when masonry styles are unavailable', () => {
  const f = fixture({ observers: false });
  const { cards } = f.galleries[0];
  const link = cards[0].querySelector('.post-card__link');
  f.flush();
  link.height = 233;
  f.event('resize');
  f.flush();
  assert.equal(cards[0].style.gridRowEnd, 'span 257');
  link.height = 270;
  link.querySelector('img').emit('error');
  f.flush();
  assert.equal(cards[0].style.gridRowEnd, 'span 294');

  const missingStyles = fixture({ row: NaN });
  missingStyles.flush();
  assert.equal(missingStyles.galleries[0].grid.hasAttribute('data-post-masonry-ready'), false);
  assert.ok(missingStyles.galleries[0].cards.every(card => card.style.gridRowEnd === ''));
});

test('empty galleries, article media galleries, and pages without galleries initialize safely', () => {
  assert.doesNotThrow(() => fixture({ collections: [] }));
  const media = fixture({ collections: [], mediaGallery: true });
  assert.equal(media.pending(), 0);
  const empty = fixture({ collections: [[]] });
  assert.equal(empty.galleries[0].filters.hidden, true);
  assert.equal(empty.pending(), 0);
});
