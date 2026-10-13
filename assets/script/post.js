(function () {
  "use strict";

  const post = document.querySelector('.post');
  const sidebar = post?.querySelector('.post__sidebar-inner');
  const related = post?.querySelector('.post__related');

  const outline = post?.querySelector('[data-post-outline]');
  if (outline) {
    const wideOutline = window.matchMedia('(min-width: 992px)');
    const setOutlineDefault = () => { outline.open = wideOutline.matches; };
    // Reset only when crossing the breakpoint; preserve manual toggles otherwise.
    wideOutline.addEventListener('change', setOutlineDefault);
    setOutlineDefault();
  }

  // Pandoc emits raw HTML headings, which Zola cannot include in page.toc.
  // Rebuild the prose portion from the rendered headings so both authoring
  // paths have the same outline and the same scroll-spy behavior.
  const proseEnd = post?.querySelector('[data-prose-toc-end]');
  const prose = post?.querySelector('.post__prose');
  if (proseEnd && prose) {
    const headings = Array.from(prose.querySelectorAll('h1, h2'));
    if (headings.length) {
      post.querySelectorAll('[data-prose-heading]').forEach((item) => item.remove());
      headings.forEach((heading, index) => {
        if (!heading.id) {
          let id = `article-section-${index + 1}`;
          while (document.getElementById(id)) id += '-section';
          heading.id = id;
        }
        const item = document.createElement('li');
        item.dataset.proseHeading = '';
        const link = document.createElement('a');
        link.href = `#${encodeURIComponent(heading.id)}`;
        link.textContent = heading.textContent.trim();
        item.append(link);
        proseEnd.before(item);
      });
    }
  }

  if (sidebar && related) {
    // Move one widget into the sticky group on desktop, restoring its original
    // reading/tab order below the article on small screens.
    const home = document.createComment('Related posts on small screens');
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

  const contentsLinks = Array.from(post?.querySelectorAll('.post__contents a') || []);
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
      const readingLine = parseFloat(window.getComputedStyle(post).scrollMarginTop) || 0;
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
      observer.observe(post);
    }
    scheduleCurrentSection();
  }

  const lightbox = post?.querySelector('[data-post-lightbox]');
  if (lightbox && typeof lightbox.showModal === 'function') {
    const image = lightbox.querySelector('[data-lightbox-image]');
    const title = lightbox.querySelector('[data-lightbox-title]');
    const caption = lightbox.querySelector('[data-lightbox-caption]');
    const count = lightbox.querySelector('[data-lightbox-count]');
    const close = lightbox.querySelector('[data-lightbox-close]');
    const viewport = lightbox.querySelector('[data-lightbox-viewport]');
    const status = lightbox.querySelector('[data-lightbox-status]');
    const triggers = Array.from(post.querySelectorAll('a[data-post-lightbox-trigger]'))
      .filter((trigger) => trigger.querySelector('img'));

    if (image && title && caption && count && close && viewport) {
      let source = null;
      let request = 0;
      let backdropPress = false;
      let description = '';
      const plainText = (element) => element?.textContent.replace(/\s+/g, ' ').trim() || '';
      const setStatus = (message) => {
        if (status) {
          status.textContent = message;
          status.hidden = !message;
        } else {
          caption.textContent = [description, message].filter(Boolean).join(' ');
        }
      };
      const openFigure = (trigger) => {
        if (lightbox.open) return true;
        const thumbnail = trigger.querySelector('img');
        const index = triggers.indexOf(trigger);
        const figureCaption = trigger.closest('figure')?.querySelector('figcaption')?.cloneNode(true);
        const captionTitle = figureCaption?.querySelector('strong');
        title.textContent = plainText(captionTitle) || `Figure ${index + 1}`;
        captionTitle?.remove();
        description = plainText(figureCaption);
        caption.textContent = description;
        count.textContent = `Figure ${index + 1} of ${triggers.length}`;
        image.alt = thumbnail.alt;
        image.hidden = true;
        image.removeAttribute('src');
        viewport.scrollTo({ left: 0, top: 0, behavior: 'instant' });
        setStatus('Loading figure…');
        const position = { trigger, x: window.scrollX, y: window.scrollY };
        try {
          lightbox.showModal();
        } catch (_) {
          return false;
        }
        source = position;
        document.documentElement.classList.add('post-lightbox-open');
        close.focus({ preventScroll: true });

        // A separate loader prevents a previous figure's late response from
        // replacing the current image or error state after reopening.
        const currentRequest = ++request;
        const loader = new Image();
        loader.onload = () => {
          if (currentRequest !== request || !lightbox.open) return;
          image.src = loader.src;
          image.width = loader.naturalWidth;
          image.height = loader.naturalHeight;
          image.hidden = false;
          setStatus('');
        };
        loader.onerror = () => {
          if (currentRequest !== request || !lightbox.open) return;
          setStatus('The full-size figure could not be loaded. Close this viewer and try again.');
        };
        loader.src = trigger.href;
        return true;
      };

      triggers.forEach((trigger) => {
        trigger.setAttribute('role', 'button');
        trigger.setAttribute('aria-haspopup', 'dialog');
        trigger.setAttribute('aria-label', `View figure: ${trigger.querySelector('img').alt}`);
        if (lightbox.id) trigger.setAttribute('aria-controls', lightbox.id);
        trigger.addEventListener('click', (event) => {
          if (event.defaultPrevented || event.button !== 0 || event.ctrlKey || event.metaKey || event.shiftKey || event.altKey) return;
          if (openFigure(trigger)) event.preventDefault();
        });
        trigger.addEventListener('keydown', (event) => {
          if (event.key !== ' ' || event.ctrlKey || event.metaKey || event.shiftKey || event.altKey) return;
          event.preventDefault();
          if (!event.repeat) openFigure(trigger);
        });
      });

      close.addEventListener('click', () => lightbox.close());
      lightbox.addEventListener('keydown', (event) => {
        if (event.key !== 'Tab' || event.defaultPrevented || event.ctrlKey || event.metaKey || event.altKey) return;
        const focusable = Array.from(lightbox.querySelectorAll('button:not(:disabled), [tabindex="0"]'))
          .filter((element) => !element.matches(':disabled') && !element.closest('[hidden]') &&
            element.getClientRects().length && window.getComputedStyle(element).visibility !== 'hidden');
        if (!focusable.length) return;
        const current = focusable.indexOf(document.activeElement);
        const next = current < 0 ? (event.shiftKey ? focusable.length - 1 : 0) :
          (current + (event.shiftKey ? -1 : 1) + focusable.length) % focusable.length;
        event.preventDefault();
        focusable[next].focus({ preventScroll: true });
      });
      const isBackdrop = (event) => {
        const bounds = lightbox.getBoundingClientRect();
        return event.target === lightbox && (event.clientX < bounds.left || event.clientX > bounds.right ||
          event.clientY < bounds.top || event.clientY > bounds.bottom);
      };
      lightbox.addEventListener('pointerdown', (event) => {
        backdropPress = event.button === 0 && isBackdrop(event);
      });
      lightbox.addEventListener('pointercancel', () => { backdropPress = false; });
      lightbox.addEventListener('click', (event) => {
        if (backdropPress && isBackdrop(event)) lightbox.close();
        backdropPress = false;
      });
      // Native dialog cancellation handles Escape.
      lightbox.addEventListener('close', () => {
        ++request;
        backdropPress = false;
        document.documentElement.classList.remove('post-lightbox-open');
        image.hidden = true;
        image.removeAttribute('src');
        if (source) {
          source.trigger.focus({ preventScroll: true });
          window.scrollTo({ left: source.x, top: source.y, behavior: 'instant' });
          source = null;
        }
      });
    }
  }

  const citation = document.getElementById('post-bibtex');
  const citationStatus = document.getElementById('post-citation')?.querySelector('[data-copy-status]');

  document.querySelectorAll('[data-copy-citation]').forEach(copyButton => {
    const resource = copyButton.closest('[data-copy-resource]');
    const copyStatus = resource?.closest('.post__resources')?.querySelector('[data-copy-status]') ||
      citationStatus;
    if (!citation || !copyStatus) return;
    const label = copyButton.querySelector('[data-copy-label]');
    const originalLabel = label?.textContent;
    const keepsFocus = Boolean(label || resource);
    const feedback = copyButton.getAttribute('data-copy-feedback') || 'BibTeX copied to clipboard.';
    let feedbackTimer = null;
    let copying = false;
    function restoreLabel() {
      if (feedbackTimer !== null) window.clearTimeout(feedbackTimer);
      feedbackTimer = null;
      if (label) label.textContent = originalLabel;
    }

    copyButton.hidden = false;
    const fallback = resource?.querySelector('[data-copy-citation-fallback]');
    if (fallback) fallback.hidden = true;
    copyButton.addEventListener('click', async () => {
      if (copying || copyButton.disabled) return;
      copying = true;
      restoreLabel();
      copyStatus.textContent = '';
      if (citationStatus) {
        citationStatus.textContent = '';
        citationStatus.classList.add('visually-hidden');
      }
      const hadFocus = document.activeElement === copyButton;
      let copied = false;
      if (keepsFocus) {
        copyButton.setAttribute('aria-disabled', 'true');
        copyButton.setAttribute('aria-busy', 'true');
      } else {
        copyButton.disabled = true;
      }
      try {
        await navigator.clipboard.writeText(citation.textContent.trim());
        copied = true;
        copyStatus.textContent = feedback;
        if (label) {
          copyStatus.classList.add('visually-hidden');
          label.textContent = feedback;
          feedbackTimer = window.setTimeout(restoreLabel, 3000);
        } else {
          copyStatus.classList.remove('visually-hidden');
        }
      } catch (_) {
        // Clipboard access can be unavailable or denied. Keep a manual path.
        const selection = window.getSelection();
        const range = document.createRange();
        range.selectNodeContents(citation);
        selection.removeAllRanges();
        selection.addRange(range);
        citation.parentElement.focus();
        // Show the manual-copy fallback beside the selected citation.
        const fallbackStatus = citationStatus || copyStatus;
        fallbackStatus.classList.remove('visually-hidden');
        fallbackStatus.textContent = 'Copy unavailable. The citation is selected; use your browser’s Copy command.';
      } finally {
        copying = false;
        if (keepsFocus) {
          copyButton.removeAttribute('aria-disabled');
          copyButton.removeAttribute('aria-busy');
        } else {
          copyButton.disabled = false;
        }
        // Disabling a focused native button can move focus to the body. Restore
        // it after success without scrolling or taking focus from another control.
        if (copied && hadFocus && document.activeElement === document.body) {
          copyButton.focus({ preventScroll: true });
        }
      }
    });
  });

  document.querySelectorAll('[data-post-gallery]').forEach((gallery) => {
    const track = gallery.querySelector('.post__slides');
    const slides = Array.from(gallery.querySelectorAll('.post__slide'));
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
