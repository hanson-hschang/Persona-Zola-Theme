(function() {
  "use strict";

  const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
  const printMedia = window.matchMedia('print');

  document.querySelectorAll('[data-badge-marquee]').forEach(root => {
    const viewport = root.querySelector('.resume__badges-viewport');
    const track = root.querySelector('.resume__badges-track');
    const original = track?.querySelector('.resume__summary-badges');
    if (!viewport || !track || !original) return;

    let enabled = false;
    let paused = false;
    let hovered = window.matchMedia('(hover: hover)').matches && root.matches(':hover');
    let keyboardMode = viewport.matches(':focus-visible');
    let keyboardFocused = keyboardMode;
    let printing = printMedia.matches;
    let cycle = 0;
    let position = 0;
    let previousTime = null;
    let frame = null;
    let gesture = null;

    function stop() {
      if (frame !== null) window.cancelAnimationFrame(frame);
      frame = null;
      previousTime = null;
    }

    function advance(time) {
      // Keep subpixels between frames; rounded scrollLeft values otherwise stall.
      if (previousTime !== null) {
        position = (position + Math.min(time - previousTime, 64) * 0.024) % cycle;
        viewport.scrollLeft = position;
      }
      previousTime = time;
      frame = window.requestAnimationFrame(advance);
    }

    function refresh() {
      const running = enabled && !paused && !hovered && !keyboardFocused &&
        !gesture?.active && !document.hidden && !printing && !printMedia.matches;
      if (!running) {
        stop();
      } else if (frame === null) {
        position = viewport.scrollLeft % cycle;
        frame = window.requestAnimationFrame(advance);
      }
    }

    function rebuild() {
      // Print styles wrap the original list; keep those measurements out of the loop.
      if (printing || printMedia.matches) {
        stop();
        return;
      }
      const oldPosition = viewport.scrollLeft;
      const oldCycle = cycle;
      stop();
      track.querySelectorAll('[data-badge-copy]').forEach(copy => copy.remove());
      const width = original.getBoundingClientRect().width;
      const gap = Number.parseFloat(window.getComputedStyle(track).columnGap) || 0;
      cycle = width + gap;
      enabled = original.children.length > 1 && !reducedMotion.matches &&
        width > 0 && viewport.clientWidth > 0;

      if (enabled) {
        // Repeat enough content to cover wide viewports throughout a complete cycle.
        const copies = Math.ceil(viewport.clientWidth / cycle) + 1;
        for (let index = 0; index < copies; index += 1) {
          const copy = original.cloneNode(true);
          copy.setAttribute('data-badge-copy', '');
          // Hide repeats from screen readers and the tab order, while preserving
          // pointer access to links and hover animations throughout the loop.
          copy.setAttribute('aria-hidden', 'true');
          copy.removeAttribute('id');
          copy.querySelectorAll('[id]').forEach(element => element.removeAttribute('id'));
          copy.querySelectorAll('a[href]').forEach(link => { link.tabIndex = -1; });
          track.append(copy);
        }
        viewport.scrollLeft = oldCycle ? (oldPosition % oldCycle) / oldCycle * cycle : 0;
      } else {
        viewport.scrollLeft = Math.min(oldPosition, Math.max(0, width - viewport.clientWidth));
      }
      root.toggleAttribute('data-badge-animated', enabled);
      refresh();
    }

    function pauseForInteraction() {
      paused = true;
      refresh();
    }

    root.addEventListener('pointerenter', event => {
      if (event.pointerType === 'mouse') { hovered = true; refresh(); }
    });
    root.addEventListener('pointerleave', event => {
      if (event.pointerType === 'mouse') {
        hovered = false;
        paused = false;
        refresh();
      }
    });
    viewport.addEventListener('focusin', () => {
      keyboardFocused = keyboardMode;
      refresh();
    });
    viewport.addEventListener('focusout', () => window.queueMicrotask(() => {
      if (!viewport.contains(document.activeElement)) {
        keyboardFocused = false;
        paused = false;
      }
      refresh();
    }));
    viewport.addEventListener('pointerdown', event => {
      pauseForInteraction();
      if ((event.button !== 0 && event.button !== 1) || event.isPrimary === false) {
        if (gesture) gesture.cancelled = true;
        return;
      }
      gesture = {
        pointerId: event.pointerId,
        x: event.clientX,
        y: event.clientY,
        scrollLeft: viewport.scrollLeft,
        started: performance.now(),
        active: true,
        cancelled: false,
      };
    }, { passive: true });
    function trackGesture(event) {
      if (!gesture?.active || event.pointerId !== gesture.pointerId) return;
      // Remember any movement, even if the pointer returns to its starting point.
      if (Math.hypot(event.clientX - gesture.x, event.clientY - gesture.y) >= 8) {
        gesture.cancelled = true;
      }
    }
    document.addEventListener('pointermove', trackGesture, { passive: true });
    document.addEventListener('pointerup', event => {
      if (!gesture?.active || event.pointerId !== gesture.pointerId) return;
      trackGesture(event);
      if (performance.now() - gesture.started >= 500) gesture.cancelled = true;
      gesture.active = false;
      refresh();
    }, { passive: true });
    document.addEventListener('pointercancel', event => {
      if (!gesture || event.pointerId !== gesture.pointerId) return;
      gesture.cancelled = true;
      gesture.active = false;
      refresh();
    }, { passive: true });
    document.addEventListener('scroll', event => {
      if (!gesture?.active) return;
      // A queued marquee scroll event can arrive just after pointerdown. Only
      // actual movement since pointerdown should invalidate an otherwise clean tap.
      if (event.target !== viewport || viewport.scrollLeft !== gesture.scrollLeft) {
        gesture.cancelled = true;
      }
    }, { capture: true, passive: true });
    viewport.addEventListener('contextmenu', () => {
      if (gesture) gesture.cancelled = true;
    });
    function guardLinkActivation(event) {
      const link = event.target.closest('a.resume__badge[href]');
      if (!link || !viewport.contains(link)) return;
      // Keep native Enter/assistive-technology activation and target="_blank".
      if (event.type === 'click' && event.detail === 0 && !event.pointerType) return;
      if (gesture && (gesture.cancelled || viewport.scrollLeft !== gesture.scrollLeft ||
        (gesture.active && performance.now() - gesture.started >= 500))) {
        event.preventDefault();
      }
    }
    viewport.addEventListener('click', guardLinkActivation, true);
    viewport.addEventListener('auxclick', guardLinkActivation, true);
    viewport.addEventListener('wheel', event => {
      if (gesture?.active && (event.deltaX || event.deltaY)) gesture.cancelled = true;
      if (event.deltaX || (event.shiftKey && event.deltaY)) pauseForInteraction();
    }, { passive: true });
    document.addEventListener('keydown', () => {
      keyboardMode = true;
      if (viewport.contains(document.activeElement)) {
        keyboardFocused = true;
        refresh();
      }
    });
    document.addEventListener('pointerdown', event => {
      // Pointer focus must not keep the strip paused after the pointer leaves it.
      keyboardMode = false;
      keyboardFocused = false;
      if (!root.contains(event.target)) {
        paused = false;
        hovered = false;
      }
      refresh();
    }, { passive: true });
    document.addEventListener('visibilitychange', refresh);
    window.addEventListener('beforeprint', () => { printing = true; refresh(); });
    window.addEventListener('afterprint', () => { printing = false; rebuild(); });
    printMedia.addEventListener('change', event => {
      printing = event.matches;
      if (printing) refresh();
      else rebuild();
    });
    reducedMotion.addEventListener('change', rebuild);
    if (typeof ResizeObserver !== 'undefined') {
      const observer = new ResizeObserver(rebuild);
      observer.observe(original);
      observer.observe(viewport);
    } else {
      window.addEventListener('resize', rebuild);
    }
    rebuild();
  });

  document.querySelectorAll('[data-skill-tabs]').forEach(root => {
    const rail = root.querySelector('.resume__skill-tabs');
    const tabs = Array.from(root.querySelectorAll('.resume__skill-tab'));
    const panels = tabs.map(tab => root.querySelector(tab.getAttribute('href')));
    if (!rail || !tabs.length || panels.some(panel => !panel)) return;

    // Keep the anchor links and complete panels usable until enhancement succeeds.
    rail.setAttribute('role', 'tablist');
    tabs.forEach((tab, index) => {
      tab.setAttribute('role', 'tab');
      tab.setAttribute('aria-controls', panels[index].id);
      panels[index].setAttribute('role', 'tabpanel');
      panels[index].tabIndex = 0;
    });
    root.setAttribute('data-tabs-ready', '');

    function select(index, reveal = false) {
      tabs.forEach((tab, current) => {
        const selected = current === index;
        tab.setAttribute('aria-selected', String(selected));
        tab.tabIndex = selected ? 0 : -1;
        panels[current].hidden = !selected;
      });
      if (reveal) {
        const bounds = rail.getBoundingClientRect();
        const tabBounds = tabs[index].getBoundingClientRect();
        if (tabBounds.left < bounds.left) rail.scrollLeft -= bounds.left - tabBounds.left;
        else if (tabBounds.right > bounds.right) rail.scrollLeft += tabBounds.right - bounds.right;
      }
    }

    tabs.forEach((tab, index) => {
      tab.addEventListener('pointerenter', event => {
        if (event.pointerType === 'mouse') select(index);
      });
      tab.addEventListener('click', event => { event.preventDefault(); select(index, true); });
      tab.addEventListener('focus', () => select(index, true));
      tab.addEventListener('keydown', event => {
        let next = index;
        if (event.key === 'ArrowRight') next = (index + 1) % tabs.length;
        else if (event.key === 'ArrowLeft') next = (index + tabs.length - 1) % tabs.length;
        else if (event.key === 'Home') next = 0;
        else if (event.key === 'End') next = tabs.length - 1;
        else if (event.key !== ' ') return;
        event.preventDefault();
        select(next, true);
        tabs[next].focus({ preventScroll: true });
      });
    });
    const linkedPanel = panels.findIndex(panel => '#' + panel.id === window.location.hash);
    select(linkedPanel < 0 ? 0 : linkedPanel);

    rail.addEventListener('wheel', event => {
      if (event.ctrlKey || rail.scrollWidth <= rail.clientWidth + 1) return;
      const delta = Math.abs(event.deltaX) > Math.abs(event.deltaY) ? event.deltaX : event.deltaY;
      const unit = event.deltaMode === 1 ? 16 : event.deltaMode === 2 ? rail.clientWidth : 1;
      const before = rail.scrollLeft;
      rail.scrollLeft += delta * unit;
      if (rail.scrollLeft !== before) event.preventDefault();
    }, { passive: false });
  });
})();
