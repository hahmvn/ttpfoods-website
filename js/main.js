(function () {
  "use strict";

  /* ---------- Language ---------- */
  var root = document.documentElement;
  var langBtns = document.querySelectorAll("[data-set-lang]");
  function setLang(lang) {
    root.setAttribute("lang", lang);
    langBtns.forEach(function (b) {
      b.setAttribute("aria-pressed", String(b.dataset.setLang === lang));
    });
    document.title = lang === "en"
      ? "About TTP Foods | Optimum solution - Lasting success"
      : "Giới thiệu TTP Foods | Giải pháp tối ưu - Thành công bền vững";
    try { localStorage.setItem("ttp-lang", lang); } catch (e) {}
  }
  langBtns.forEach(function (b) {
    b.addEventListener("click", function () { setLang(b.dataset.setLang); });
  });
  var saved = null;
  try { saved = localStorage.getItem("ttp-lang"); } catch (e) {}
  setLang(saved === "en" ? "en" : "vi");

  /* ---------- Mobile menu ---------- */
  var menuBtn = document.querySelector(".menu-toggle");
  var nav = document.querySelector(".main-nav");
  if (menuBtn && nav) {
    menuBtn.addEventListener("click", function () {
      var open = nav.classList.toggle("open");
      menuBtn.setAttribute("aria-expanded", String(open));
    });
    nav.addEventListener("click", function (e) {
      if (e.target.closest("a")) { nav.classList.remove("open"); menuBtn.setAttribute("aria-expanded", "false"); }
    });
  }

  /* ---------- Sub-nav active state ---------- */
  var subLinks = Array.prototype.slice.call(document.querySelectorAll(".subnav a"));
  var sections = subLinks.map(function (a) { return document.querySelector(a.getAttribute("href")); }).filter(Boolean);
  function updateActive() {
    var y = window.scrollY + 160;
    var current = sections[0];
    sections.forEach(function (s) { if (s.offsetTop <= y) current = s; });
    subLinks.forEach(function (a) {
      var on = a.getAttribute("href") === "#" + current.id;
      a.classList.toggle("active", on);
      if (on && a.scrollIntoView && window.innerWidth < 760) {
        var ul = a.parentElement.parentElement;
        ul.scrollLeft = a.offsetLeft - 16;
      }
    });
    toTop.classList.toggle("show", window.scrollY > 600);
  }
  var toTop = document.querySelector(".to-top");
  toTop.addEventListener("click", function () { window.scrollTo({ top: 0 }); });
  window.addEventListener("scroll", updateActive, { passive: true });
  updateActive();

  /* ---------- Product category tabs ---------- */
  var tabs = Array.prototype.slice.call(document.querySelectorAll(".cat-tabs [role=tab]"));
  function selectTab(tab, focus) {
    tabs.forEach(function (t) {
      var sel = t === tab;
      t.setAttribute("aria-selected", String(sel));
      t.tabIndex = sel ? 0 : -1;
      document.getElementById(t.getAttribute("aria-controls")).hidden = !sel;
    });
    if (focus) tab.focus();
    if (tab.scrollIntoView) tab.scrollIntoView({ block: "nearest", inline: "nearest" });
  }
  tabs.forEach(function (tab, i) {
    tab.addEventListener("click", function () { selectTab(tab, false); });
    tab.addEventListener("keydown", function (e) {
      var next = null;
      if (e.key === "ArrowRight") next = tabs[(i + 1) % tabs.length];
      else if (e.key === "ArrowLeft") next = tabs[(i - 1 + tabs.length) % tabs.length];
      else if (e.key === "Home") next = tabs[0];
      else if (e.key === "End") next = tabs[tabs.length - 1];
      if (next) { e.preventDefault(); selectTab(next, true); }
    });
  });

  /* ---------- Leadership bio modal ---------- */
  var dlg = document.getElementById("bio");
  var lastTrigger = null;
  document.querySelectorAll(".member .more").forEach(function (btn) {
    btn.addEventListener("click", function () {
      var tpl = document.getElementById(btn.dataset.bio);
      dlg.querySelector(".bio-content").innerHTML = tpl.innerHTML;
      lastTrigger = btn;
      document.body.classList.add("modal-open");
      if (typeof dlg.showModal === "function") dlg.showModal();
      else dlg.setAttribute("open", "");
      dlg.querySelector(".bio-close").focus();
    });
  });
  dlg.addEventListener("click", function (e) {
    if (e.target === dlg || e.target.closest(".bio-close")) dlg.close();
  });
  dlg.addEventListener("close", function () {
    document.body.classList.remove("modal-open");
    if (lastTrigger) lastTrigger.focus();
  });

  /* ---------- Reveal on scroll ---------- */
  if ("IntersectionObserver" in window) {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        if (en.isIntersecting) { en.target.classList.add("in"); io.unobserve(en.target); }
      });
    }, { threshold: 0.12 });
    document.querySelectorAll(".reveal").forEach(function (el) { io.observe(el); });
  } else {
    document.querySelectorAll(".reveal").forEach(function (el) { el.classList.add("in"); });
  }

  document.getElementById("year").textContent = new Date().getFullYear();
})();
