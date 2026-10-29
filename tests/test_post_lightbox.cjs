const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');
const vm = require('node:vm');

const script = fs.readFileSync(path.join(__dirname, '../static/assets/script/post.js'), 'utf8');

// Exercise the shipped script with controllable image responses and touch events.
function fixture({ figures = 3, modal = true, failOpen = false, setup } = {}) {
  let document;
  class Element {
    constructor(tag, attributes = {}, text = '') {
      this.tag = tag;
      this.nodeType = tag === '#text' ? 3 : 1;
      this.attributes = new Map(Object.entries(attributes));
      this.childNodes = [];
      this.listeners = new Map();
      this.hidden = false;
      this._text = this.nodeType === 3 ? text : '';
      if (this.nodeType === 1 && text) this.append(new Element('#text', {}, text));
      this.classList = {
        add: (name) => this.attributes.set('class', name),
        remove: () => this.attributes.delete('class'),
        contains: (name) => (this.attributes.get('class') || '').split(' ').includes(name),
      };
    }
    get children() { return this.childNodes.filter(child => child.nodeType === 1); }
    get parentElement() { return this.parent?.nodeType === 1 ? this.parent : null; }
    get previousSibling() { return this.parent?.childNodes[this.parent.childNodes.indexOf(this) - 1] || null; }
    get nextSibling() { return this.parent?.childNodes[this.parent.childNodes.indexOf(this) + 1] || null; }
    append(child) {
      child.remove();
      child.parent = this;
      this.childNodes.push(child);
      return child;
    }
    before(sibling) {
      sibling.remove();
      sibling.parent = this.parent;
      this.parent.childNodes.splice(this.parent.childNodes.indexOf(this), 0, sibling);
    }
    remove() {
      if (this.parent) this.parent.childNodes = this.parent.childNodes.filter(child => child !== this);
      this.parent = null;
    }
    set textContent(value) {
      this.childNodes.forEach(child => { child.parent = null; });
      this.childNodes = [];
      if (this.nodeType === 3) this._text = value;
      else if (value) this.append(new Element('#text', {}, value));
    }
    get textContent() { return this._text + this.childNodes.map(child => child.textContent).join(''); }
    get href() { return this.hasAttribute('href') ? new URL(this.getAttribute('href'), document.baseURI).href : ''; }
    set href(value) { this.setAttribute('href', value); }
    get src() { return this.hasAttribute('src') ? new URL(this.getAttribute('src'), document.baseURI).href : ''; }
    set src(value) { this.setAttribute('src', value); }
    get alt() { return this.getAttribute('alt') || ''; }
    set alt(value) { this.setAttribute('alt', value); }
    setAttribute(name, value) { this.attributes.set(name, value); }
    removeAttribute(name) { this.attributes.delete(name); }
    getAttribute(name) { return this.attributes.get(name) ?? null; }
    hasAttribute(name) { return this.attributes.has(name); }
    matches(selector) {
      if (this.nodeType !== 1) return false;
      if (selector === ':disabled') return !!this.disabled;
      if (selector === '[hidden]') return this.hidden;
      if (selector === 'button:not(:disabled), [tabindex="0"]') {
        return (this.tag === 'button' && !this.disabled) || this.getAttribute('tabindex') === '0';
      }
      if (selector.includes(',')) return selector.split(',').some(part => this.matches(part.trim()));
      if (selector.includes(' ')) {
        const parts = selector.split(/\s+/);
        return this.matches(parts.pop()) && !!this.parent?.closest(parts.join(' '));
      }
      const match = /^(\w+)?(?:\.([\w-]+))?(?:\[([\w-]+)\])?$/.exec(selector);
      return !!match && (!match[1] || this.tag === match[1]) &&
        (!match[2] || this.classList.contains(match[2])) && (!match[3] || this.attributes.has(match[3]));
    }
    querySelectorAll(selector) {
      return this.children.flatMap(child => [
        ...(child.matches(selector) ? [child] : []), ...child.querySelectorAll(selector),
      ]);
    }
    querySelector(selector) { return this.querySelectorAll(selector)[0] || null; }
    closest(selector) { return this.matches(selector) ? this : this.parent?.closest(selector); }
    cloneNode() {
      const clone = new Element(this.tag, Object.fromEntries(this.attributes), this._text);
      this.childNodes.forEach(child => clone.append(child.cloneNode()));
      return clone;
    }
    focus(options) { document.activeElement = this; this.focusOptions = options; }
    scrollTo(options) { this.scrollPosition = options; }
    getClientRects() { return this.hidden ? [] : [{}]; }
    getBoundingClientRect() { return { left: 20, right: 370, top: 100, bottom: 600 }; }
    addEventListener(type, callback) {
      const callbacks = this.listeners.get(type) || [];
      callbacks.push(callback);
      this.listeners.set(type, callbacks);
    }
  }
  document = new Element('document');
  document.baseURI = 'https://example.com/project/posts/note/';
  document.documentElement = document;
  document.getElementById = () => null;
  document.createElement = tag => new Element(tag);
  const post = document.append(new Element('article', { class: 'post' }));
  const prose = post.append(new Element('div', { class: 'post__prose' }));
  Array.from({ length: figures }, (_, index) => {
    const figure = prose.append(new Element('figure'));
    const trigger = figure.append(new Element('a', { 'data-post-lightbox-trigger': '' }));
    trigger.href = `https://example.com/figure-${index + 1}.png`;
    trigger.append(new Element('img', { src: trigger.href, alt: `Image ${index + 1}` }));
    const caption = figure.append(new Element('figcaption'));
    caption.append(new Element('strong', {}, `Title ${index + 1}.`));
    caption.append(new Element('span', {}, ` Caption ${index + 1}. `));
    return trigger;
  });
  const content = setup?.({ post, prose, el: (tag, attributes, text) => new Element(tag, attributes, text) });
  const lightbox = post.append(new Element('dialog', { 'data-post-lightbox': '' }));
  lightbox.id = 'figures';
  lightbox.open = false;
  lightbox.showCount = 0;
  if (modal) lightbox.showModal = () => {
    if (failOpen) throw new Error('Dialog unavailable');
    lightbox.open = true;
    lightbox.showCount += 1;
  };
  lightbox.close = () => { lightbox.open = false; dispatch('close', lightbox); };
  const element = (name, tag = 'div', parent = lightbox) =>
    parent.append(new Element(tag, { [`data-lightbox-${name}`]: '' }));
  const count = element('count');
  const title = element('title');
  const close = element('close', 'button');
  const previous = element('previous', 'button');
  const next = element('next', 'button');
  previous.hidden = next.hidden = true;
  const viewport = element('viewport');
  viewport.setAttribute('tabindex', '0');
  const image = element('image', 'img', viewport);
  const status = element('status', 'p', viewport);
  const caption = element('caption');
  const loaders = [];
  const window = {
    scrollX: 4, scrollY: 900, visualViewport: { scale: 1 },
    scrollTo(options) { this.scrollPosition = options; },
    getComputedStyle: () => ({ visibility: 'visible' }),
    setTimeout() { assert.fail('The lightbox must never schedule autoplay'); },
    setInterval() { assert.fail('The lightbox must never schedule autoplay'); },
  };
  function dispatch(type, target, properties = {}) {
    const event = {
      type, target, button: 0, defaultPrevented: false,
      preventDefault() { this.defaultPrevented = true; }, ...properties,
    };
    for (let node = target; node; node = node.parent) {
      (node.listeners.get(type) || []).forEach(callback => callback(event));
    }
    return event;
  }
  const touch = (x, y, identifier = 1) => ({ clientX: x, clientY: y, identifier });
  const touchEvent = (type, touches, changedTouches = touches) =>
    dispatch(type, viewport, { touches, changedTouches });
  vm.runInNewContext(script, {
    document, window, URL, Image: class { constructor() { loaders.push(this); } },
  });
  const triggers = post.querySelectorAll('a[data-post-lightbox-trigger]');
  return {
    document, window, triggers, lightbox, count, title, caption, close, previous, next, content,
    viewport, image, status, loaders, dispatch, touch, touchEvent,
    open(index = 0) { return dispatch('click', triggers[index]); },
    swipe(dx, dy = 0) {
      touchEvent('touchstart', [touch(180, 120)]);
      touchEvent('touchmove', [touch(180 + dx, 120 + dy)]);
      touchEvent('touchend', [], [touch(180 + dx, 120 + dy)]);
    },
    load(index = loaders.length - 1, width = 1200, height = 300) {
      Object.assign(loaders[index], { naturalWidth: width, naturalHeight: height });
      loaders[index].onload();
    },
  };
}

test('opening sets figure metadata and dimensions without changing the article caption', () => {
  const f = fixture();
  assert.equal(f.open(1).defaultPrevented, true);
  assert.equal(f.lightbox.open, true);
  assert.equal(f.document.classList.contains('post-lightbox-open'), true);
  assert.equal(f.title.textContent, 'Title 2.');
  assert.equal(f.caption.textContent, 'Caption 2.');
  assert.equal(f.count.textContent, 'Figure 2 of 3');
  assert.equal(f.image.alt, 'Image 2');
  assert.equal(f.image.hidden, true);
  assert.equal(f.status.textContent, 'Loading figure…');
  assert.equal(f.triggers[1].closest('figure').querySelector('strong').textContent, 'Title 2.');
  f.load();
  assert.equal(f.image.src, f.triggers[1].href);
  assert.equal(f.image.width, 1200);
  assert.equal(f.image.height, 300);
  assert.equal(f.image.hidden, false);
  assert.equal(f.status.hidden, true);
  assert.equal(f.document.activeElement, f.close);
});

test('buttons loop in both directions and closing restores the original opener and scroll', () => {
  const f = fixture();
  f.open();
  f.previous.focus();
  f.dispatch('click', f.previous);
  assert.equal(f.count.textContent, 'Figure 3 of 3');
  assert.equal(f.document.activeElement, f.previous);
  f.dispatch('click', f.next);
  assert.equal(f.count.textContent, 'Figure 1 of 3');
  f.caption.scrollTo({ left: 0, top: 160 });
  f.viewport.scrollTo({ left: 0, top: 240 });
  f.dispatch('click', f.next);
  assert.equal(f.title.textContent, 'Title 2.');
  assert.equal(f.caption.textContent, 'Caption 2.');
  assert.equal(f.count.textContent, 'Figure 2 of 3');
  assert.equal(f.caption.scrollPosition.top, 0);
  assert.equal(f.viewport.scrollPosition.top, 0);
  assert.equal(f.lightbox.showCount, 1);
  f.window.scrollY = 1200;
  f.dispatch('click', f.close);
  assert.equal(f.document.activeElement, f.triggers[0]);
  assert.equal(f.triggers[0].focusOptions.preventScroll, true);
  assert.equal(f.window.scrollPosition.top, 900);
  assert.equal(f.window.scrollPosition.left, 4);
  assert.equal(f.document.classList.contains('post-lightbox-open'), false);
});

test('left/right swipes loop, leave focus in place, and never navigate automatically on load', () => {
  const f = fixture();
  f.open();
  f.swipe(80);
  assert.equal(f.count.textContent, 'Figure 3 of 3');
  f.load();
  assert.equal(f.count.textContent, 'Figure 3 of 3');
  assert.equal(f.loaders.length, 2);
  f.swipe(-100, 15);
  assert.equal(f.count.textContent, 'Figure 1 of 3');
  f.swipe(-80);
  assert.equal(f.count.textContent, 'Figure 2 of 3');
  assert.equal(f.document.activeElement, f.close);
});

test('taps, short drags, vertical scrolling, and gestures that turn horizontal are ignored', () => {
  const f = fixture();
  f.open();
  for (const [x, y] of [[0, 0], [-39, 0], [-40, 60], [-90, 70]]) f.swipe(x, y);
  f.touchEvent('touchstart', [f.touch(180, 120)]);
  f.touchEvent('touchmove', [f.touch(175, 150)]);
  f.touchEvent('touchend', [], [f.touch(70, 125)]);
  assert.equal(f.loaders.length, 1);
  assert.equal(f.count.textContent, 'Figure 1 of 3');
});

test('multi-touch, pinch zoom, and cancelled gestures cannot switch figures', () => {
  const f = fixture();
  f.open();
  f.touchEvent('touchstart', [f.touch(180, 120)]);
  f.touchEvent('touchstart', [f.touch(180, 120), f.touch(210, 120, 2)]);
  f.touchEvent('touchend', [f.touch(80, 120)], [f.touch(210, 120, 2)]);
  f.touchEvent('touchend', [], [f.touch(80, 120)]);
  f.touchEvent('touchstart', [f.touch(180, 120)]);
  f.touchEvent('touchcancel', [], [f.touch(90, 120)]);
  f.touchEvent('touchend', [], [f.touch(80, 120)]);
  f.window.visualViewport.scale = 2;
  f.swipe(-90);
  f.window.visualViewport.scale = 1;
  f.touchEvent('touchstart', [f.touch(180, 120)]);
  f.window.visualViewport.scale = 1.2;
  f.touchEvent('touchend', [], [f.touch(80, 120)]);
  assert.equal(f.loaders.length, 1);
  f.window.visualViewport.scale = 1;
  f.swipe(-90);
  assert.equal(f.count.textContent, 'Figure 2 of 3');
});

test('arrow keys loop and Tab traps focus across the visible controls', () => {
  const f = fixture();
  f.open();
  const key = (key, properties = {}) => f.dispatch('keydown', f.document.activeElement, { key, ...properties });
  assert.equal(key('ArrowLeft').defaultPrevented, true);
  assert.equal(f.count.textContent, 'Figure 3 of 3');
  key('ArrowRight');
  assert.equal(f.count.textContent, 'Figure 1 of 3');
  for (const modifier of ['ctrlKey', 'metaKey', 'altKey', 'shiftKey']) {
    assert.equal(key('ArrowRight', { [modifier]: true }).defaultPrevented, false);
  }
  assert.equal(f.count.textContent, 'Figure 1 of 3');
  key('Tab');
  assert.equal(f.document.activeElement, f.previous);
  key('Tab');
  assert.equal(f.document.activeElement, f.next);
  key('Tab');
  assert.equal(f.document.activeElement, f.viewport);
  key('Tab');
  assert.equal(f.document.activeElement, f.close);
  key('Tab', { shiftKey: true });
  assert.equal(f.document.activeElement, f.viewport);
});

test('late image loads/errors cannot replace a newer figure or affect a reopened dialog', () => {
  const f = fixture();
  f.open();
  f.swipe(-90);
  f.load(1, 500, 800);
  f.load(0);
  f.loaders[0].onerror();
  assert.equal(f.image.src, f.triggers[1].href);
  assert.equal(f.image.width, 500);
  assert.equal(f.status.hidden, true);
  f.lightbox.close();
  f.open(2);
  f.load(1);
  f.loaders[1].onerror();
  assert.equal(f.image.hidden, true);
  assert.equal(f.status.textContent, 'Loading figure…');
  f.loaders[2].onerror();
  assert.match(f.status.textContent, /could not be loaded/);
  f.swipe(-90);
  f.load(3);
  assert.equal(f.image.src, f.triggers[0].href);
  assert.equal(f.status.hidden, true);
  f.lightbox.close();
  f.load(3);
  assert.equal(f.image.hidden, true);
  assert.equal(f.image.src, '');
});

test('single figures hide navigation and ignore gestures and arrow keys', () => {
  const f = fixture({ figures: 1 });
  f.open();
  assert.equal(f.previous.hidden, true);
  assert.equal(f.next.hidden, true);
  f.swipe(-90);
  assert.equal(f.dispatch('keydown', f.close, { key: 'ArrowRight' }).defaultPrevented, false);
  assert.equal(f.loaders.length, 1);
  assert.equal(f.count.textContent, 'Figure 1 of 1');
});

test('native image links survive modified clicks and unavailable dialogs', () => {
  const f = fixture();
  for (const properties of [{ ctrlKey: true }, { metaKey: true }, { shiftKey: true }, { button: 1 }]) {
    assert.equal(f.dispatch('click', f.triggers[0], properties).defaultPrevented, false);
  }
  assert.equal(f.lightbox.open, false);
  assert.equal(fixture({ modal: false }).open().defaultPrevented, false);
  assert.equal(fixture({ failOpen: true }).open().defaultPrevented, false);
  assert.doesNotThrow(() => fixture({ figures: 0 }));
});

test('unlinked HTML figures and Markdown images become clickable in document order', () => {
  const f = fixture({ figures: 0, setup({ prose, el }) {
    const figure = prose.append(el('figure'));
    const figureImage = figure.append(el('img', { src: 'chart.png', alt: 'Chart' }));
    const paragraph = prose.append(el('p'));
    const markdownImage = paragraph.append(el('img', { src: '../plot.svg', alt: 'Plot' }));
    return { figure, figureImage, paragraph, markdownImage };
  } });
  assert.equal(f.triggers.length, 2);
  assert.equal(f.triggers[0].parent, f.content.figure);
  assert.equal(f.triggers[1].parent, f.content.paragraph);
  assert.equal(f.content.figureImage.parent, f.triggers[0]);
  assert.equal(f.content.markdownImage.parent, f.triggers[1]);
  assert.equal(f.triggers[0].href, 'https://example.com/project/posts/note/chart.png');
  assert.equal(f.triggers[1].href, 'https://example.com/project/posts/plot.svg');
  f.open();
  assert.equal(f.count.textContent, 'Figure 1 of 2');
  f.swipe(-90);
  assert.equal(f.count.textContent, 'Figure 2 of 2');
  assert.equal(f.title.textContent, 'Figure 2');
  assert.equal(f.image.alt, 'Plot');
  f.load();
  assert.equal(f.image.src, f.content.markdownImage.src);
});

test('responsive pictures retain their source children inside one clickable wrapper', () => {
  const f = fixture({ figures: 0, setup({ prose, el }) {
    const figure = prose.append(el('figure'));
    const picture = figure.append(el('picture'));
    const source = picture.append(el('source', { srcset: 'large.avif', type: 'image/avif' }));
    const image = picture.append(el('img', { src: 'fallback.png', alt: 'Responsive chart' }));
    return { figure, picture, source, image };
  } });
  assert.equal(f.triggers.length, 1);
  assert.equal(f.triggers[0].parent, f.content.figure);
  assert.equal(f.content.picture.parent, f.triggers[0]);
  assert.equal(f.content.source.parent, f.content.picture);
  assert.equal(f.content.image.parent, f.content.picture);
  assert.equal(f.content.source.getAttribute('srcset'), 'large.avif');
  assert.equal(f.triggers[0].querySelectorAll('a').length, 0);
  f.open();
  assert.equal(f.loaders[0].src, f.content.image.src);
});

test('existing image links join the viewer while links to other pages retain navigation', () => {
  const f = fixture({ figures: 0, setup({ prose, el }) {
    const imageLink = prose.append(el('a', { href: '/assets/original.JPG?download=1' }));
    imageLink.append(el('img', { src: 'thumbnail.jpg', alt: 'Image link' }));
    const pageLink = prose.append(el('a', { href: '/research/' }));
    pageLink.append(el('img', { src: 'cover.jpg', alt: 'Research page' }));
    return { imageLink, pageLink };
  } });
  assert.deepEqual(f.triggers, [f.content.imageLink]);
  assert.equal(f.content.imageLink.querySelectorAll('a').length, 0);
  assert.equal(f.content.pageLink.hasAttribute('data-post-lightbox-trigger'), false);
  assert.equal(f.dispatch('click', f.content.pageLink).defaultPrevented, false);
  f.open();
  assert.equal(f.loaders[0].src, 'https://example.com/assets/original.JPG?download=1');
});

test('authored captions and links remain intact while unlinked figures use their own image source', () => {
  const f = fixture({ figures: 0, setup({ prose, el }) {
    const figure = prose.append(el('figure'));
    const image = figure.append(el('img', { src: 'thumbnail.png', alt: 'Detailed chart' }));
    const caption = figure.append(el('figcaption'));
    const paragraph = caption.append(el('p'));
    const title = paragraph.append(el('strong', {}, 'Chart title.'));
    paragraph.append(el('#text', {}, ' Caption. '));
    const reference = paragraph.append(el('a', { href: '/paper/' }, 'Reference'));
    paragraph.append(el('#text', {}, '. '));
    const opener = paragraph.append(el('a', { href: 'original.png' }, 'Open full-size figure'));
    paragraph.append(el('#text', {}, '.'));
    return { figure, image, caption, paragraph, title, reference, opener };
  } });
  assert.equal(f.triggers[0].href, f.content.image.src);
  assert.equal(f.content.opener.parent, f.content.paragraph);
  assert.equal(f.content.caption.textContent.trim(), 'Chart title. Caption. Reference. Open full-size figure.');
  assert.equal(f.content.reference.href, 'https://example.com/paper/');
  assert.equal(f.content.title.textContent, 'Chart title.');
  f.open();
  assert.equal(f.title.textContent, 'Chart title.');
  assert.equal(f.caption.textContent, 'Caption. Reference. Open full-size figure.');
  assert.equal(f.loaders[0].src, f.triggers[0].href);
});

test('authored parenthesized image links and link-only paragraphs are preserved', () => {
  for (const label of ['View the original image', 'See full-resolution figure', 'Download larger image']) {
    const f = fixture({ figures: 0, setup({ prose, el }) {
      const figure = prose.append(el('figure'));
      figure.append(el('img', { src: 'figure.webp' }));
      const caption = figure.append(el('figcaption'));
      caption.append(el('#text', {}, 'Figure description. ('));
      caption.append(el('a', { href: 'figure.webp' }, label));
      caption.append(el('#text', {}, '). '));
      const paragraph = caption.append(el('p'));
      paragraph.append(el('a', { href: 'figure.webp' }, 'Open full-size figure'));
      paragraph.append(el('#text', {}, '.'));
      return { caption, paragraph };
    } });
    assert.equal(f.content.caption.textContent.trim(),
      `Figure description. (${label}). Open full-size figure.`, label);
    assert.equal(f.content.paragraph.parent, f.content.caption, label);
    assert.equal(f.content.caption.querySelectorAll('a').length, 2, label);
  }
});

test('caption references, image links, and attribution images remain unchanged', () => {
  const f = fixture({ figures: 0, setup({ prose, el }) {
    const figure = prose.append(el('figure'));
    const existing = figure.append(el('a', { href: 'current.png' }));
    existing.append(el('img', { src: 'thumbnail.png' }));
    const caption = figure.append(el('figcaption'));
    const reference = caption.append(el('a', { href: '/paper/' }, 'Open original image'));
    const otherImage = caption.append(el('a', { href: 'other.png' }, 'Open full-size figure'));
    const sourceImage = caption.append(el('a', { href: 'current.png' }, 'Source image credit'));
    const captionImage = caption.append(el('img', { src: 'credit-badge.svg' }));
    return { caption, reference, otherImage, sourceImage, captionImage };
  } });
  assert.equal(f.triggers.length, 1);
  assert.deepEqual(f.content.caption.querySelectorAll('a'),
    [f.content.reference, f.content.otherImage, f.content.sourceImage]);
  assert.equal(f.content.captionImage.parent, f.content.caption);
});

test('an unrelated generic caption image link cannot replace an unlinked figure source', () => {
  const f = fixture({ figures: 0, setup({ prose, el }) {
    const figure = prose.append(el('figure'));
    const image = figure.append(el('img', { src: 'current.png', alt: 'Current chart' }));
    const caption = figure.append(el('figcaption'));
    const otherImage = caption.append(el('a', { href: 'other.png' }, 'See image'));
    return { image, caption, otherImage };
  } });
  assert.equal(f.triggers.length, 1);
  assert.equal(f.triggers[0].href, f.content.image.src);
  assert.equal(f.content.otherImage.parent, f.content.caption);
  assert.equal(f.content.otherImage.href, 'https://example.com/project/posts/note/other.png');
  f.open();
  assert.equal(f.loaders[0].src, 'https://example.com/project/posts/note/current.png');
});

test('without native dialogs newly clickable images use their own source and preserve captions', () => {
  const f = fixture({ figures: 0, modal: false, setup({ prose, el }) {
    const figure = prose.append(el('figure'));
    figure.append(el('img', { src: 'thumb.jpg', alt: 'Chart' }));
    const caption = figure.append(el('figcaption'));
    caption.append(el('a', { href: 'full.jpg' }, 'Open full-size figure'));
    return { figure, caption };
  } });
  assert.equal(f.triggers.length, 1);
  assert.equal(f.triggers[0].href, 'https://example.com/project/posts/note/thumb.jpg');
  assert.equal(f.triggers[0].getAttribute('role'), null);
  assert.equal(f.open().defaultPrevented, false);
  assert.equal(f.lightbox.open, false);
  assert.equal(f.content.caption.querySelectorAll('a').length, 1);
  assert.equal(f.content.caption.querySelector('a').href, 'https://example.com/project/posts/note/full.jpg');
  assert.equal(f.content.caption.textContent, 'Open full-size figure');
});
