(function () {
  "use strict";

  function initSharing() {
    document.querySelectorAll("[data-share]").forEach((share) => {
      const toggle = share.querySelector("[data-share-toggle]");
      const menu = share.querySelector(".share-menu");
      if (!toggle || !menu) return;

      function closeMenu(restoreFocus = false) {
        menu.hidden = true;
        toggle.setAttribute("aria-expanded", "false");
        if (restoreFocus) toggle.focus();
      }

      // Keep the unenhanced HTML's working links available when JavaScript is absent.
      share.classList.add("share--enhanced");
      toggle.hidden = false;
      closeMenu();

      toggle.addEventListener("click", () => {
        const opening = menu.hidden;
        menu.hidden = !opening;
        toggle.setAttribute("aria-expanded", String(opening));
      });

      share.addEventListener("keydown", (event) => {
        if (event.key === "Escape" && !menu.hidden) {
          event.preventDefault();
          closeMenu(true);
        }
      });

      document.addEventListener("click", (event) => {
        if (!share.contains(event.target)) closeMenu();
      });

      share.addEventListener("focusout", (event) => {
        if (event.relatedTarget && !share.contains(event.relatedTarget)) closeMenu();
      });
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initSharing);
  } else {
    initSharing();
  }
})();
