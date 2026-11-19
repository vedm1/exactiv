/* Theme button and mobile menu (EXW3). The site follows the system light or dark setting. This script lets a visitor
   choose the other one. It stores one word, "light" or "dark", in this browser (localStorage) and
   nothing else. The menu stores nothing. No cookie, no request, no data leaves the device (W-G3, G11). Without this script the
   button stays hidden and the system setting applies. It loads in the head so the page never flashes. */
(function () {
  'use strict';

  var KEY = 'ex-theme';
  var root = document.documentElement;

  function stored() {
    try {
      var v = window.localStorage.getItem(KEY);
      return v === 'light' || v === 'dark' ? v : null;
    } catch (e) { return null; }
  }

  function save(v) {
    try { window.localStorage.setItem(KEY, v); } catch (e) { /* storage blocked: the choice lasts for this page only */ }
  }

  function effective() {
    var set = root.getAttribute('data-theme');
    if (set === 'light' || set === 'dark') { return set; }
    var dark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
    return dark ? 'dark' : 'light';
  }

  root.classList.add('js'); // CSS collapses the menu on narrow screens only when this script runs

  var choice = stored();
  if (choice) { root.setAttribute('data-theme', choice); }

  document.addEventListener('DOMContentLoaded', function () {
    var header = document.querySelector('.ex-header');
    var menu = document.getElementById('menu-toggle');
    if (header && menu) {
      var setOpen = function (open) {
        header.classList.toggle('is-open', open);
        menu.setAttribute('aria-expanded', open ? 'true' : 'false');
      };
      menu.addEventListener('click', function () { setOpen(!header.classList.contains('is-open')); });
      document.addEventListener('keydown', function (e) {
        if (e.key === 'Escape' && header.classList.contains('is-open')) { setOpen(false); menu.focus(); }
      });
    }
    var button = document.getElementById('theme-toggle');
    if (!button) { return; }
    function paint() { button.setAttribute('aria-pressed', effective() === 'dark' ? 'true' : 'false'); }
    button.addEventListener('click', function () {
      var next = effective() === 'dark' ? 'light' : 'dark';
      root.setAttribute('data-theme', next);
      save(next);
      paint();
    });
    paint();
    button.hidden = false;
  });
})();
