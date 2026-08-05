(function () {
  "use strict";

  var deferredInstallPrompt = null;
  var refreshingForUpdate = false;
  var standalone = window.matchMedia("(display-mode: standalone)").matches || window.navigator.standalone === true;
  var host = document.querySelector(".paper, .page, .not-found") || document.body;
  var footer = document.querySelector(".colophon, footer.foot, .foot, footer");

  var panel = document.createElement("section");
  panel.className = "ddb-pwa-panel";
  panel.hidden = true;
  panel.setAttribute("role", "region");
  panel.setAttribute("aria-labelledby", "ddb-pwa-title");

  var eyebrow = document.createElement("p");
  eyebrow.className = "ddb-pwa-eyebrow";
  eyebrow.textContent = "David's Daily Bread app";

  var title = document.createElement("h2");
  title.id = "ddb-pwa-title";

  var copy = document.createElement("p");
  copy.className = "ddb-pwa-copy";

  var actions = document.createElement("div");
  actions.className = "ddb-pwa-actions";

  var primaryAction = document.createElement("button");
  primaryAction.className = "ddb-pwa-action";
  primaryAction.type = "button";

  var closeAction = document.createElement("button");
  closeAction.className = "ddb-pwa-action ddb-pwa-action-secondary";
  closeAction.type = "button";
  closeAction.textContent = "Close";

  var status = document.createElement("p");
  status.className = "ddb-pwa-status";
  status.setAttribute("aria-live", "polite");

  actions.appendChild(primaryAction);
  actions.appendChild(closeAction);
  panel.appendChild(eyebrow);
  panel.appendChild(title);
  panel.appendChild(copy);
  panel.appendChild(actions);
  panel.appendChild(status);
  host.appendChild(panel);

  var launcher = document.createElement("button");
  launcher.className = "ddb-pwa-launch";
  launcher.type = "button";
  launcher.textContent = "Install app";
  launcher.hidden = standalone;

  if (footer) {
    footer.appendChild(document.createTextNode(" · "));
    footer.appendChild(launcher);
  } else {
    var launchWrap = document.createElement("div");
    launchWrap.className = "ddb-pwa-launch-wrap";
    launchWrap.appendChild(launcher);
    host.appendChild(launchWrap);
  }

  var networkStatus = document.createElement("div");
  networkStatus.className = "ddb-pwa-network";
  networkStatus.setAttribute("role", "status");
  networkStatus.setAttribute("aria-live", "polite");
  networkStatus.textContent = "Offline: showing pages saved on this device";
  networkStatus.hidden = navigator.onLine;
  document.body.appendChild(networkStatus);

  function isIos() {
    return /iphone|ipad|ipod/i.test(navigator.userAgent) ||
      (navigator.platform === "MacIntel" && navigator.maxTouchPoints > 1);
  }

  function installGuidance() {
    if (isIos()) {
      return "In Safari, tap Share, then choose Add to Home Screen.";
    }
    if (!("serviceWorker" in navigator)) {
      return "This browser does not offer the installable app. You can bookmark the website and keep reading by RSS.";
    }
    return "Open your browser menu and choose Install app or Add to Home Screen.";
  }

  function showInstallPanel() {
    panel.hidden = false;
    title.textContent = "The bakery, ready from your home screen";
    copy.textContent = "News and Scripture each morning. An evening Field Guide with useful tools and workflows. Loved by God.";
    primaryAction.textContent = deferredInstallPrompt ? "Install now" : "How to install";
    primaryAction.onclick = requestInstall;
    status.textContent = deferredInstallPrompt ? "Your browser is ready to install this website." : installGuidance();
    panel.scrollIntoView({ block: "nearest", behavior: "auto" });
    primaryAction.focus();
  }

  function requestInstall() {
    if (!deferredInstallPrompt) {
      status.textContent = installGuidance();
      return;
    }
    var promptEvent = deferredInstallPrompt;
    deferredInstallPrompt = null;
    promptEvent.prompt();
    promptEvent.userChoice.then(function (choice) {
      if (choice.outcome === "accepted") {
        status.textContent = "Installation accepted.";
        launcher.hidden = true;
      } else {
        status.textContent = "Nothing changed. Install whenever it is useful.";
      }
    });
  }

  function showUpdatePanel(registration) {
    if (!registration.waiting || !navigator.serviceWorker.controller) return;
    panel.hidden = false;
    title.textContent = "A fresher app shell is ready";
    copy.textContent = "Refresh to use it. Editions, the archive, and corrections are still checked online first.";
    primaryAction.textContent = "Refresh now";
    primaryAction.onclick = function () {
      refreshingForUpdate = true;
      registration.waiting.postMessage({ type: "ACTIVATE_UPDATE" });
      status.textContent = "Refreshing the app shell.";
    };
    status.textContent = "Your notes remain on this device.";
  }

  launcher.addEventListener("click", showInstallPanel);
  closeAction.addEventListener("click", function () {
    panel.hidden = true;
    if (!launcher.hidden) {
      launcher.focus();
      return;
    }
    var fallbackFocus = document.querySelector(".masthead-art-link, a");
    if (fallbackFocus) fallbackFocus.focus();
  });

  window.addEventListener("beforeinstallprompt", function (event) {
    event.preventDefault();
    deferredInstallPrompt = event;
    launcher.hidden = standalone;
  });

  window.addEventListener("appinstalled", function () {
    standalone = true;
    deferredInstallPrompt = null;
    launcher.hidden = true;
    panel.hidden = true;
  });

  window.addEventListener("offline", function () {
    networkStatus.hidden = false;
  });

  window.addEventListener("online", function () {
    networkStatus.hidden = true;
  });

  if (!("serviceWorker" in navigator)) return;

  navigator.serviceWorker.addEventListener("controllerchange", function () {
    if (refreshingForUpdate) window.location.reload();
  });

  window.addEventListener("load", function () {
    navigator.serviceWorker.register("/service-worker.js", {
      scope: "/",
      updateViaCache: "none"
    }).then(function (registration) {
      showUpdatePanel(registration);
      registration.update().catch(function () {});
      registration.addEventListener("updatefound", function () {
        var installing = registration.installing;
        if (!installing) return;
        installing.addEventListener("statechange", function () {
          if (installing.state === "installed") showUpdatePanel(registration);
        });
      });
    }).catch(function () {
      if (!panel.hidden) status.textContent = "Offline reading is unavailable in this browser right now.";
    });
  });
})();
