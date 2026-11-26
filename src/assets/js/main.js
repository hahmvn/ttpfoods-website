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

  /* ---------- Contact form ---------- */
  var form = document.querySelector("form.cform");
  if (form) {
    var en = form.getAttribute("data-lang") === "en";
    var msg = {
      sending: en ? "Sending…" : "Đang gửi…",
      ok: en ? "Thank you! Your request has been sent. We will contact you shortly." : "Cảm ơn bạn! Yêu cầu đã được gửi, chúng tôi sẽ liên hệ lại sớm.",
      fail: en ? "Sorry, the request could not be sent. Please email info@ttpfoods.vn or call 0904 004 199." : "Rất tiếc, chưa gửi được yêu cầu. Vui lòng email info@ttpfoods.vn hoặc gọi 0904 004 199.",
      mail: en ? "Your email app has been opened with the request – please press Send there." : "Ứng dụng email đã được mở sẵn nội dung – vui lòng bấm Gửi trong ứng dụng email."
    };
    // Pre-select product group from ?sp=<key> (quote buttons on product pages)
    var params = new URLSearchParams(location.search);
    var sp = params.get("sp"), pn = params.get("p");
    var msgBox = form.querySelector("#f-message");
    if (pn && msgBox && !msgBox.value) msgBox.value = (en ? "Product of interest: " : "Sản phẩm quan tâm: ") + pn + "\n";
    if (sp) {
      var opt = form.querySelector('#f-product option[data-key="' + sp + '"]');
      if (opt) opt.selected = true;
    }
    var status = form.querySelector(".cform-status");
    var btn = form.querySelector('button[type="submit"]');
    function setStatus(text, kind) {
      status.hidden = false; status.textContent = text; status.className = "cform-status is-" + kind;
    }
    function validate() {
      var first = null;
      ["f-name", "f-email", "f-message", "f-consent"].forEach(function (id) {
        var el = document.getElementById(id);
        var ok = el.type === "checkbox" ? el.checked : el.value.trim() !== "" && el.checkValidity();
        el.toggleAttribute("aria-invalid", !ok);
        if (!ok) el.setAttribute("aria-describedby", id + "-err"); else el.removeAttribute("aria-describedby");
        el.closest(".field").classList.toggle("has-error", !ok);
        if (!ok && !first) first = el;
      });
      if (first) first.focus();
      return !first;
    }
    form.addEventListener("submit", function (e) {
      e.preventDefault();
      if (form.botcheck && form.botcheck.checked) return;
      if (!validate()) return;
      var now = new Date(), pad = function (n) { return (n < 10 ? "0" : "") + n; };
      form.submitted_at.value = now.getFullYear() + "-" + pad(now.getMonth() + 1) + "-" + pad(now.getDate()) + " " +
        pad(now.getHours()) + ":" + pad(now.getMinutes()) + " (UTC" + (now.getTimezoneOffset() > 0 ? "-" : "+") +
        pad(Math.floor(Math.abs(now.getTimezoneOffset()) / 60)) + ")";
      var data = new FormData(form);
      var key = form.getAttribute("data-key");
      if (!key) {
        // No form service configured yet: hand over to the visitor's e-mail app
        var lines = [];
        data.forEach(function (v, k) {
          if (["access_key", "subject", "from_name", "botcheck", "language"].indexOf(k) === -1 && v) lines.push(k + ": " + v);
        });
        location.href = "mailto:" + form.getAttribute("data-mailto") + "?subject=" +
          encodeURIComponent(data.get("subject") + " – " + data.get("name")) + "&body=" + encodeURIComponent(lines.join("\n"));
        setStatus(msg.mail, "ok");
        return;
      }
      btn.disabled = true; setStatus(msg.sending, "info");
      data.set("subject", data.get("subject") + " – " + data.get("name") + (data.get("product") ? " – " + data.get("product") : ""));
      fetch(form.action, { method: "POST", headers: { Accept: "application/json" }, body: data })
        .then(function (r) { return r.json(); })
        .then(function (j) {
          if (j && j.success) { form.reset(); setStatus(msg.ok, "ok"); }
          else setStatus(msg.fail, "error");
        })
        .catch(function () { setStatus(msg.fail, "error"); })
        .then(function () { btn.disabled = false; });
    });
    form.addEventListener("input", function (e) {
      var f = e.target.closest(".field");
      if (f && f.classList.contains("has-error")) { f.classList.remove("has-error"); e.target.removeAttribute("aria-invalid"); }
    });
  }

  /* ---------- Products overview: filter groups by application (?ud=bakery) ---------- */
  var filter = document.querySelector(".app-filter");
  if (filter) {
    var cards = Array.prototype.slice.call(document.querySelectorAll("#group-grid > li"));
    var statusEl = document.querySelector(".app-filter-status");
    var isEn = document.documentElement.lang === "en";
    var apply = function (app, push) {
      var shown = 0;
      cards.forEach(function (li) {
        var ok = !app || (" " + li.getAttribute("data-apps") + " ").indexOf(" " + app + " ") > -1;
        li.hidden = !ok; if (ok) { shown++; li.classList.add("in"); }
      });
      filter.querySelectorAll(".chip-btn").forEach(function (b) { b.setAttribute("aria-pressed", String(b.getAttribute("data-app") === app)); });
      if (statusEl) statusEl.textContent = app ? (isEn ? shown + " product groups" : shown + " nhóm sản phẩm") : "";
      if (push && history.replaceState) history.replaceState(null, "", app ? "?ud=" + app : location.pathname);
    };
    filter.addEventListener("click", function (e) {
      var b = e.target.closest(".chip-btn"); if (b) apply(b.getAttribute("data-app"), true);
    });
    var initial = new URLSearchParams(location.search).get("ud");
    if (initial && filter.querySelector('[data-app="' + initial + '"]')) apply(initial, false);
  }

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
