(function () {
  "use strict";

  const project = document.querySelector('.project');
  const sidebar = project?.querySelector('.project__sidebar-inner');
  const related = project?.querySelector('.project__related');

  if (sidebar && related) {
    // Move one widget into the sticky group on desktop, restoring its original
    // reading/tab order below the article on small screens.
    const home = document.createComment('Related projects on small screens');
    related.before(home);
    const wideScreen = window.matchMedia('(min-width: 992px)');
    const placeRelated = () => {
      const focused = related.contains(document.activeElement) ? document.activeElement : null;
      if (wideScreen.matches) sidebar.append(related);
      else home.after(related);
      focused?.focus({ preventScroll: true });
    };
    wideScreen.addEventListener('change', placeRelated);
    placeRelated();
  }

  const contentsLinks = Array.from(project?.querySelectorAll('.project__contents a') || []);
  const sections = contentsLinks.flatMap((link) => {
    const url = new URL(link.href);
    if (url.origin !== window.location.origin || url.pathname !== window.location.pathname) return [];
    try {
      const target = document.getElementById(decodeURIComponent(url.hash.slice(1)));
      return target ? [{ link, target }] : [];
    } catch (_) {
      return [];
    }
  });

  if (sections.length) {
    let activeLink = null;
    let frame = null;

    const updateCurrentSection = () => {
      frame = null;
      // Match anchor-link clearance so clicking and scrolling select the same
      // section underneath the site's desktop navigation.
      const readingLine = parseFloat(window.getComputedStyle(project).scrollMarginTop) || 0;
      let current = null;
      sections.forEach(({ link, target }) => {
        if (target.getBoundingClientRect().top <= readingLine + 1) current = link;
      });
      if (!current && sections[0].target.getBoundingClientRect().top < window.innerHeight / 2) {
        current = sections[0].link;
      }
      // A short final section may never reach the reading line.
      if (window.scrollY > 0 && window.scrollY + window.innerHeight >= document.documentElement.scrollHeight - 2) {
        current = sections[sections.length - 1].link;
      }
      if (current === activeLink) return;
      activeLink?.removeAttribute('aria-current');
      current?.setAttribute('aria-current', 'location');
      activeLink = current;
    };

    const scheduleCurrentSection = () => {
      if (frame === null) frame = window.requestAnimationFrame(updateCurrentSection);
    };
    window.addEventListener('scroll', scheduleCurrentSection, { passive: true });
    window.addEventListener('resize', scheduleCurrentSection);
    window.addEventListener('hashchange', scheduleCurrentSection);
    window.addEventListener('load', scheduleCurrentSection);
    // Lazy media and font loading can move headings without a scroll event.
    if ('ResizeObserver' in window) {
      const observer = new ResizeObserver(scheduleCurrentSection);
      observer.observe(project);
    }
    scheduleCurrentSection();
  }

  const copyButton = document.querySelector('[data-copy-citation]');
  const citation = document.getElementById('project-bibtex');
  const copyStatus = document.querySelector('[data-copy-status]');

  if (copyButton && citation && copyStatus) {
    copyButton.hidden = false;
    copyButton.addEventListener('click', async () => {
      copyStatus.textContent = '';
      copyButton.disabled = true;
      try {
        await navigator.clipboard.writeText(citation.textContent.trim());
        copyStatus.textContent = 'BibTeX copied to clipboard.';
      } catch (_) {
        // Clipboard access can be unavailable or denied. Keep a manual path.
        const selection = window.getSelection();
        const range = document.createRange();
        range.selectNodeContents(citation);
        selection.removeAllRanges();
        selection.addRange(range);
        citation.parentElement.focus();
        copyStatus.textContent = 'Copy unavailable. The citation is selected; use your browser’s Copy command.';
      } finally {
        copyButton.disabled = false;
      }
    });
  }

  document.querySelectorAll('[data-project-gallery]').forEach((gallery) => {
    const track = gallery.querySelector('.project__slides');
    const slides = Array.from(gallery.querySelectorAll('.project__slide'));
    const controls = gallery.querySelector('[data-gallery-controls]');
    if (!track || slides.length < 2 || !controls) return;

    const previous = controls.querySelector('[data-gallery-previous]');
    const next = controls.querySelector('[data-gallery-next]');
    const status = controls.querySelector('[data-gallery-status]');
    const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
    let current = 0;
    let frame = null;

    const update = () => {
      const left = track.getBoundingClientRect().left;
      let distance = Infinity;
      slides.forEach((slide, index) => {
        const offset = Math.abs(slide.getBoundingClientRect().left - left);
        if (offset < distance) {
          distance = offset;
          current = index;
        }
      });
      previous.disabled = current === 0;
      next.disabled = current === slides.length - 1;
      const label = `${current + 1} / ${slides.length}`;
      if (status.textContent !== label) status.textContent = label;
      slides.forEach((slide, index) => {
        if (index !== current) slide.querySelectorAll('video').forEach((video) => video.pause());
      });
      frame = null;
    };

    const scheduleUpdate = () => {
      if (frame === null) frame = window.requestAnimationFrame(update);
    };

    const move = (direction) => {
      const index = Math.max(0, Math.min(slides.length - 1, current + direction));
      track.scrollTo({
        left: track.scrollLeft + slides[index].getBoundingClientRect().left - track.getBoundingClientRect().left,
        behavior: reducedMotion.matches ? 'auto' : 'smooth'
      });
    };

    previous.addEventListener('click', () => move(-1));
    next.addEventListener('click', () => move(1));
    // Arrow keys on the track complement native touch/scroll and button controls.
    track.addEventListener('keydown', (event) => {
      if (event.target !== track || !['ArrowLeft', 'ArrowRight'].includes(event.key)) return;
      event.preventDefault();
      move(event.key === 'ArrowRight' ? 1 : -1);
    });
    track.addEventListener('scroll', scheduleUpdate, { passive: true });
    window.addEventListener('resize', scheduleUpdate);
    controls.hidden = false;
    update();
  });

})();
