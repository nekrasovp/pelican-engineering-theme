(function () {
  "use strict";

  var storageKey = "pelican-engineering-theme";
  var light = "light";
  var dark = "dark";
  var root = document.documentElement;
  var button = document.querySelector("[data-pet-theme-toggle]");
  var themeColor = document.querySelector("[data-pet-theme-color]");

  if (!button) {
    return;
  }

  var label = button.querySelector("[data-pet-theme-toggle-label]");

  function storedTheme() {
    try {
      return localStorage.getItem(storageKey) === dark ? dark : light;
    } catch (_error) {
      return light;
    }
  }

  function persist(theme) {
    try {
      localStorage.setItem(storageKey, theme);
    } catch (_error) {
      /* The DOM state remains usable for this page when storage is unavailable. */
    }
  }

  function applyTheme(theme, shouldPersist) {
    var isDark = theme === dark;

    if (isDark) {
      root.dataset.theme = dark;
    } else {
      root.removeAttribute("data-theme");
    }

    button.setAttribute("aria-pressed", String(isDark));
    button.setAttribute("aria-label", isDark ? "Use light theme" : "Use dark theme");
    if (label) {
      label.textContent = isDark ? "Light theme" : "Dark theme";
    }
    if (themeColor) {
      themeColor.setAttribute("content", isDark ? "#101712" : "#f7f8f3");
    }
    if (shouldPersist) {
      persist(isDark ? dark : light);
    }
  }

  applyTheme(storedTheme(), false);
  button.hidden = false;
  button.addEventListener("click", function () {
    applyTheme(root.dataset.theme === dark ? light : dark, true);
  });
}());
