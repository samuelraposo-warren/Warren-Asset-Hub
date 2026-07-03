/* ============================================================
   app.js — comportamentos globais da interface
   Por enquanto: busca/filtro automático nas listagens.
   ============================================================ */
(function () {
  "use strict";

  var FOCUS_KEY = "autosubmit_focus";
  var DEBOUNCE_MS = 400;

  /* -------- Busca automática ("digitou = consultou") -------- */
  function initAutoSubmit() {
    var forms = document.querySelectorAll("form[data-autosubmit]");
    forms.forEach(function (form) {
      var timer = null;

      // Campos de texto: aguarda o usuário parar de digitar (debounce).
      form.querySelectorAll(
        'input[type="text"], input[type="search"], input:not([type])'
      ).forEach(function (input) {
        input.addEventListener("input", function () {
          if (timer) clearTimeout(timer);
          timer = setTimeout(function () {
            rememberFocus(input);
            form.submit();
          }, DEBOUNCE_MS);
        });
      });

      // Selects e datas: aplica na hora que muda.
      form.querySelectorAll("select, input[type='date']").forEach(function (el) {
        el.addEventListener("change", function () {
          rememberFocus(el);
          form.submit();
        });
      });
    });

    restoreFocus();
  }

  function rememberFocus(el) {
    try {
      var info = { name: el.name || "", id: el.id || "" };
      if (typeof el.selectionStart === "number") {
        info.caret = el.selectionStart;
      }
      sessionStorage.setItem(FOCUS_KEY, JSON.stringify(info));
    } catch (e) {
      /* sessionStorage pode estar indisponível — ignora */
    }
  }

  function restoreFocus() {
    var raw;
    try {
      raw = sessionStorage.getItem(FOCUS_KEY);
      sessionStorage.removeItem(FOCUS_KEY);
    } catch (e) {
      return;
    }
    if (!raw) return;

    var info;
    try {
      info = JSON.parse(raw);
    } catch (e) {
      return;
    }

    var el = null;
    if (info.id) el = document.getElementById(info.id);
    if (!el && info.name) el = document.querySelector('[name="' + info.name + '"]');
    if (!el) return;

    el.focus();
    // Recoloca o cursor no fim do texto digitado.
    if (typeof info.caret === "number" && typeof el.setSelectionRange === "function") {
      try {
        var pos = Math.min(info.caret, el.value.length);
        el.setSelectionRange(pos, pos);
      } catch (e) {
        /* alguns tipos de input não suportam setSelectionRange */
      }
    }
  }

  /* -------- Sino de notificações -------- */
  function initNotifications() {
    var root = document.getElementById("notifRoot");
    var btn = document.getElementById("notifBtn");
    if (!root || !btn) return;

    btn.addEventListener("click", function (e) {
      e.stopPropagation();
      var open = root.classList.toggle("open");
      btn.setAttribute("aria-expanded", open ? "true" : "false");
    });

    document.addEventListener("click", function (e) {
      if (!root.contains(e.target)) {
        root.classList.remove("open");
        btn.setAttribute("aria-expanded", "false");
      }
    });

    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape") {
        root.classList.remove("open");
        btn.setAttribute("aria-expanded", "false");
      }
    });
  }

  function init() {
    initAutoSubmit();
    initNotifications();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
