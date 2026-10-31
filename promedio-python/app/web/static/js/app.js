/* Calculadora Académica 3.0 · Interacciones locales sin dependencias externas */
(function () {
  "use strict";

  function iniciarMenu() {
    var boton = document.getElementById("menu-boton");
    var sidebar = document.getElementById("sidebar");
    var velo = document.getElementById("velo");

    if (!boton || !sidebar || !velo) {
      return;
    }

    function abrir() {
      sidebar.classList.add("abierto");
      velo.classList.add("visible");
      boton.setAttribute("aria-expanded", "true");
    }

    function cerrar() {
      sidebar.classList.remove("abierto");
      velo.classList.remove("visible");
      boton.setAttribute("aria-expanded", "false");
    }

    boton.addEventListener("click", function () {
      if (sidebar.classList.contains("abierto")) {
        cerrar();
      } else {
        abrir();
      }
    });

    velo.addEventListener("click", cerrar);

    sidebar.addEventListener("click", function (evento) {
      if (evento.target.closest("a.nav")) {
        cerrar();
      }
    });

    document.addEventListener("keydown", function (evento) {
      if (evento.key === "Escape") {
        cerrar();
      }
    });
  }

  function iniciarFlash() {
    var flash = document.getElementById("flash");
    if (!flash) {
      return;
    }

    var cerrar = flash.querySelector(".cerrar-flash");
    if (cerrar) {
      cerrar.addEventListener("click", function () {
        flash.remove();
      });
    }

    window.setTimeout(function () {
      if (flash.isConnected) {
        flash.style.transition = "opacity .4s ease";
        flash.style.opacity = "0";
        window.setTimeout(function () {
          if (flash.isConnected) {
            flash.remove();
          }
        }, 450);
      }
    }, 7000);
  }

  function iniciarConfirmaciones() {
    var formularios = document.querySelectorAll("form[data-confirmar]");
    Array.prototype.forEach.call(formularios, function (formulario) {
      formulario.addEventListener("submit", function (evento) {
        var mensaje = formulario.getAttribute("data-confirmar");
        if (mensaje && !window.confirm(mensaje)) {
          evento.preventDefault();
        }
      });
    });
  }

  function iniciarFiltros() {
    var selects = document.querySelectorAll("select[data-autofiltrar]");
    Array.prototype.forEach.call(selects, function (select) {
      select.addEventListener("change", function () {
        if (select.form) {
          select.form.submit();
        }
      });
    });
  }

  function iniciarTeclas() {
    document.addEventListener("keydown", function (evento) {
      if ((evento.ctrlKey || evento.metaKey) && evento.key.toLowerCase() === "r") {
        // Deja que el navegador recargue; no se intercepta para no romper el flujo.
        return;
      }
    });
  }

  document.addEventListener("DOMContentLoaded", function () {
    iniciarMenu();
    iniciarFlash();
    iniciarConfirmaciones();
    iniciarFiltros();
    iniciarTeclas();
  });
})();
