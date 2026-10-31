(function () {
  "use strict";

  document.querySelectorAll('[data-post-gallery]').forEach(gallery => {
    const grid = gallery.querySelector('[data-post-grid]');
    if (!grid) return;

    const entries = Array.from(grid.querySelectorAll('.post-card')).map(card => {
      let categories = [];
      try {
        const value = JSON.parse(card.dataset.postCategories || '[]');
        if (Array.isArray(value)) categories = value.filter(category => typeof category === 'string');
      } catch (_) {
        // An invalid label payload must not hide an otherwise readable post.
      }
      return { card, link: card.querySelector('.post-card__link'), categories: new Set(categories) };
    });
    if (!entries.length) return;

    let frame = null;
    function layout() {
      frame = null;
      grid.setAttribute('data-post-masonry-ready', '');
      const style = window.getComputedStyle(grid);
      const row = Number.parseFloat(style.gridAutoRows);
      const gap = Number.parseFloat(style.rowGap) || 0;
      if (!Number.isFinite(row) || row <= 0) {
        // Keep the ordinary responsive grid when the masonry styles are absent.
        grid.removeAttribute('data-post-masonry-ready');
        entries.forEach(({ card }) => { card.style.gridRowEnd = ''; });
        return;
      }

      // Measure the natural link height, rather than a grid item already spanning
      // rows. Read first, then write, to avoid repeated layout between cards.
      const spans = entries.map(({ card, link }) => {
        if (card.hidden || !link) return '';
        const height = link.getBoundingClientRect().height;
        if (!height) return '';
        const padding = Number.parseFloat(window.getComputedStyle(card).paddingBottom) || 0;
        return `span ${Math.ceil((height + padding + gap) / (row + gap))}`;
      });
      entries.forEach(({ card }, index) => {
        if (card.style.gridRowEnd !== spans[index]) card.style.gridRowEnd = spans[index];
      });
    }
    function scheduleLayout() {
      if (frame === null) frame = window.requestAnimationFrame(layout);
    }

    const filters = gallery.querySelector('[data-post-filters]');
    const buttons = Array.from(filters?.querySelectorAll('button[data-post-filter]') || []);
    if (buttons.length) {
      function select(button) {
        const category = button.dataset.postFilter;
        const focused = document.activeElement;
        buttons.forEach(candidate => {
          candidate.setAttribute('aria-pressed', String(candidate === button));
        });
        entries.forEach(({ card, categories }) => {
          card.hidden = category !== '' && !categories.has(category);
          // Native button activation keeps keyboard focus on the control. Also
          // retain a useful focus target if a pointer activation hides a link.
          if (card.hidden && card.contains(focused)) button.focus({ preventScroll: true });
        });
        scheduleLayout();
      }
      buttons.forEach(button => button.addEventListener('click', () => select(button)));
      select(buttons.find(button => button.dataset.postFilter === '') || buttons[0]);
      filters.hidden = false;
    }

    if ('ResizeObserver' in window) {
      const observer = new window.ResizeObserver(scheduleLayout);
      observer.observe(grid);
      entries.forEach(({ link }) => { if (link) observer.observe(link); });
    }
    grid.querySelectorAll('img').forEach(image => {
      image.addEventListener('load', scheduleLayout);
      image.addEventListener('error', scheduleLayout);
    });
    window.addEventListener('resize', scheduleLayout);
    window.addEventListener('load', scheduleLayout);
    document.fonts?.ready.then(scheduleLayout);
    // Filtering and layout use no animation, preserving DOM and keyboard order
    // and respecting reduced-motion preferences without an alternate code path.
    scheduleLayout();
  });
})();
