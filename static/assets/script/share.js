(function () {
  "use strict";

  function initSharing() {
    document.querySelectorAll("[data-share]").forEach((share) => {
      const toggle = share.querySelector("[data-share-toggle]");
      const menu = share.querySelector(".share-menu");
      const copy = share.querySelector("[data-share-copy]");
      const status = share.querySelector("[role='status']");
      if (!toggle || !menu || !copy || !status) return;

      function closeMenu(restoreFocus = false) {
        menu.hidden = true;
        toggle.setAttribute("aria-expanded", "false");
        if (restoreFocus) toggle.focus();
      }

      // Keep the unenhanced HTML's working links available when JavaScript is absent.
      share.classList.add("share--enhanced");
      toggle.hidden = false;
      copy.hidden = false;
      closeMenu();

      toggle.addEventListener("click", () => {
        const opening = menu.hidden;
        menu.hidden = !opening;
        toggle.setAttribute("aria-expanded", String(opening));
        if (opening) status.textContent = "";
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

      copy.addEventListener("click", async () => {
        const permalink = copy.dataset.shareUrl;
        copy.disabled = true;
        status.textContent = "";
        try {
          if (!navigator.clipboard || !navigator.clipboard.writeText) {
            throw new Error("Clipboard unavailable");
          }
          await navigator.clipboard.writeText(permalink);
          status.textContent = "Link copied.";
        } catch (error) {
          status.textContent = "Could not copy. Use the Permalink link to copy the address.";
        } finally {
          copy.disabled = false;
        }
      });
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initSharing);
  } else {
    initSharing();
  }
})();
