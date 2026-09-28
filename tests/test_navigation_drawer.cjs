const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');
const vm = require('node:vm');

const script = fs.readFileSync(path.join(__dirname, '../static/assets/script/home.js'), 'utf8');

function element(parent = null) {
  const listeners = new Map();
  const attributes = new Map();
  const classes = new Set();
  return {
    parent,
    hidden: false,
    classList: {
      add(name) { classes.add(name); },
      remove(name) { classes.delete(name); },
      contains(name) { return classes.has(name); },
      toggle(name, force) {
        if (force === true) {
          classes.add(name);
          return true;
        }
        if (force === false || classes.has(name)) {
          classes.delete(name);
          return false;
        }
        classes.add(name);
        return true;
      },
    },
    setAttribute(name, value) { attributes.set(name, String(value)); },
    getAttribute(name) { return attributes.get(name) ?? null; },
    hasAttribute(name) { return attributes.has(name); },
    addEventListener(type, callback) {
      const callbacks = listeners.get(type) || [];
      callbacks.push(callback);
      listeners.set(type, callbacks);
    },
    emit(type, properties = {}) {
      const event = { type, target: this, preventDefault() { this.defaultPrevented = true; }, ...properties };
      (listeners.get(type) || []).forEach(callback => callback(event));
      return event;
    },
    contains(target) {
      for (let node = target; node; node = node.parent) {
        if (node === this) return true;
      }
      return false;
    },
    focus() {},
  };
}

function fixture({ mobile = true } = {}) {
  const document = element();
  const window = element();
  const header = element();
  const navmenu = element(header);
  const navLink = element(navmenu);
  const dropdownToggle = element(navmenu);
  const submenu = element(navmenu);
  const toggle = element(); // The floating button is outside #header in the template.
  const outside = element();
  toggle.classList.add('bi-list');
  toggle.setAttribute('aria-expanded', 'false');
  dropdownToggle.setAttribute('aria-controls', 'subsections');
  dropdownToggle.setAttribute('aria-expanded', 'false');

  document.querySelector = selector => ({
    '#header': header,
    '.nav-toggle': toggle,
    '#navmenu': navmenu,
  })[selector] || null;
  document.querySelectorAll = selector => ({
    '#navmenu a': [navLink],
    '.navmenu .navmenu__dropdown-toggle': [dropdownToggle],
  })[selector] || [];
  document.getElementById = id => id === 'subsections' ? submenu : null;
  window.innerWidth = mobile ? 390 : 1200;
  window.matchMedia = () => ({ matches: mobile });
  vm.runInNewContext(script, { document, window, console: { warn() {} } });
  document.emit('DOMContentLoaded');

  return {
    document, header, navmenu, navLink, dropdownToggle, submenu, toggle, outside,
    open() { return header.classList.contains('header__navmenu__show'); },
  };
}

test('outside pointerdown folds the mobile drawer and restores its toggle state', () => {
  const f = fixture();
  f.toggle.emit('click');
  f.dropdownToggle.emit('click');
  assert.equal(f.open(), true);
  assert.equal(f.toggle.getAttribute('aria-expanded'), 'true');
  assert.equal(f.toggle.classList.contains('bi-x'), true);
  assert.equal(f.dropdownToggle.getAttribute('aria-expanded'), 'true');
  assert.equal(f.submenu.classList.contains('dropdown-active'), true);

  f.document.emit('pointerdown', { target: f.outside });
  assert.equal(f.open(), false);
  assert.equal(f.toggle.getAttribute('aria-expanded'), 'false');
  assert.equal(f.toggle.classList.contains('bi-list'), true);
  assert.equal(f.toggle.classList.contains('bi-x'), false);
  assert.equal(f.dropdownToggle.getAttribute('aria-expanded'), 'false');
  assert.equal(f.submenu.classList.contains('dropdown-active'), false);
});

test('pointerdown inside the drawer or on its floating toggle does not dismiss it', () => {
  const f = fixture();
  f.toggle.emit('click');
  f.document.emit('pointerdown', { target: f.navLink });
  assert.equal(f.open(), true);
  f.dropdownToggle.emit('click');
  assert.equal(f.dropdownToggle.getAttribute('aria-expanded'), 'true');
  f.document.emit('pointerdown', { target: f.dropdownToggle });
  assert.equal(f.open(), true);
  f.document.emit('pointerdown', { target: f.toggle });
  assert.equal(f.open(), true);
});

test('outside pointerdown does not change navigation at desktop width', () => {
  const f = fixture({ mobile: false });
  f.toggle.emit('click');
  f.document.emit('pointerdown', { target: f.outside });
  assert.equal(f.open(), true);
  assert.equal(f.toggle.getAttribute('aria-expanded'), 'true');
});

test('mobile nav links continue to close the drawer', () => {
  const f = fixture();
  f.toggle.emit('click');
  f.navLink.emit('click');
  assert.equal(f.open(), false);
  assert.equal(f.toggle.getAttribute('aria-expanded'), 'false');
});
