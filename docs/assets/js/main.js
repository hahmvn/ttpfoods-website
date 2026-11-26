(function () {
  "use strict";

  /* ---------- Mobile menu ---------- */
  var menuBtn = document.querySelector(".menu-toggle");
  var nav = document.getElementById("main-nav");
  function setMenu(open) {
    if (!menuBtn || !nav) return;
    nav.classList.toggle("open", open);
    document.body.classList.toggle("nav-open", open);
    menuBtn.setAttribute("aria-expanded", String(open));
    var lang = document.documentElement.lang;
    menuBtn.setAttribute("aria-label", open ? (lang === "en" ? "Close menu" : "Đóng menu") : (lang === "en" ? "Open menu" : "Mở menu"));
  }
  if (menuBtn && nav) {
    menuBtn.addEventListener("click", function () { setMenu(!nav.classList.contains("open")); });
    nav.addEventListener("click", function (e) { if (e.target.closest("a")) setMenu(false); });
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape" && nav.classList.contains("open")) { setMenu(false); menuBtn.focus(); }
    });
    window.addEventListener("resize", function () { if (window.innerWidth > 960) setMenu(false); });
  }

  /* ---------- Back to top ---------- */
  var toTop = document.querySelector(".to-top");
  if (toTop) {
    toTop.addEventListener("click", function () { window.scrollTo({ top: 0 }); });
    var onScroll = function () { toTop.classList.toggle("show", window.scrollY > 600); };
    window.addEventListener("scroll", onScroll, { passive: true });
    onScroll();
  }

  /* ---------- Product category tabs (deep-linkable: /san-pham/#gelatin) ---------- */
  var tabs = Array.prototype.slice.call(document.querySelectorAll(".cat-tabs [role=tab]"));
  function selectTab(tab, focus, updateHash) {
    tabs.forEach(function (t) {
      var sel = t === tab;
      t.setAttribute("aria-selected", String(sel));
      t.tabIndex = sel ? 0 : -1;
      document.getElementById(t.getAttribute("aria-controls")).hidden = !sel;
    });
    if (focus) tab.focus();
    if (tab.scrollIntoView) tab.scrollIntoView({ block: "nearest", inline: "nearest" });
    if (updateHash && history.replaceState) history.replaceState(null, "", "#" + tab.getAttribute("aria-controls").replace(/^p-/, ""));
  }
  tabs.forEach(function (tab, i) {
    tab.addEventListener("click", function () { selectTab(tab, false, true); });
    tab.addEventListener("keydown", function (e) {
      var next = null;
      if (e.key === "ArrowRight") next = tabs[(i + 1) % tabs.length];
      else if (e.key === "ArrowLeft") next = tabs[(i - 1 + tabs.length) % tabs.length];
      else if (e.key === "Home") next = tabs[0];
      else if (e.key === "End") next = tabs[tabs.length - 1];
      if (next) { e.preventDefault(); selectTab(next, true, true); }
    });
  });
  function tabFromHash() {
    var id = location.hash.slice(1);
    if (!id) return;
    if (id.indexOf("p-") !== 0) id = "p-" + id;
    var tab = document.querySelector('.cat-tabs [aria-controls="' + id + '"]');
    if (tab) {
      selectTab(tab, false, false);
      var list = document.querySelector(".cat-tabs");
      var header = document.querySelector(".site-header");
      if (list) window.scrollTo({ top: list.getBoundingClientRect().top + window.scrollY - (header ? header.offsetHeight : 0) - 16 });
    }
  }
  if (tabs.length) { tabFromHash(); window.addEventListener("hashchange", tabFromHash); }

  /* ---------- Map: load Google Maps only when the visitor asks for it ---------- */
  document.querySelectorAll(".map-frame[data-map-src]").forEach(function (box) {
    var btn = box.querySelector(".map-load");
    if (!btn) return;
    btn.addEventListener("click", function () {
      var f = document.createElement("iframe");
      f.src = box.getAttribute("data-map-src");
      f.title = box.getAttribute("data-map-title") || "Map";
      f.loading = "lazy";
      f.referrerPolicy = "no-referrer-when-downgrade";
      f.setAttribute("allowfullscreen", "");
      box.innerHTML = "";
      box.appendChild(f);
      box.classList.add("is-loaded");
    });
  });

  /* ---------- Reveal on scroll ---------- */
  var items = document.querySelectorAll(".reveal");
  if ("IntersectionObserver" in window) {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        if (en.isIntersecting) { en.target.classList.add("in"); io.unobserve(en.target); }
      });
    }, { threshold: 0.12 });
    items.forEach(function (el) { io.observe(el); });
  } else {
    items.forEach(function (el) { el.classList.add("in"); });
  }
})();
