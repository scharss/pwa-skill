/*
 * Service worker registration and install helpers.
 *
 * Useful events:
 *   document.addEventListener('pwa:installable', ...)  -> safe to show the install button
 *   document.addEventListener('pwa:update', ...)       -> a new version is available
 *
 * API:
 *   PWA.isStandalone()   -> true when already running installed
 *   PWA.isIOS()          -> true on iPhone/iPad
 *   PWA.canInstall()     -> true when the browser allows the prompt
 *   PWA.promptInstall()  -> opens the native install dialog
 */

(function () {
  if ('serviceWorker' in navigator) {
    window.addEventListener('load', function () {
      navigator.serviceWorker
        .register('/sw.js')
        .then(function (registration) {
          registration.addEventListener('updatefound', function () {
            const worker = registration.installing;
            if (!worker) return;
            worker.addEventListener('statechange', function () {
              if (worker.state === 'installed' && navigator.serviceWorker.controller) {
                document.dispatchEvent(
                  new CustomEvent('pwa:update', { detail: registration })
                );
              }
            });
          });
        })
        .catch(function (error) {
          console.warn('Service worker registration failed:', error);
        });
    });
  }

  let deferredPrompt = null;

  window.addEventListener('beforeinstallprompt', function (event) {
    event.preventDefault();
    deferredPrompt = event;
    document.dispatchEvent(new CustomEvent('pwa:installable'));
  });

  window.addEventListener('appinstalled', function () {
    deferredPrompt = null;
  });

  window.PWA = {
    isStandalone: function () {
      return (
        window.matchMedia('(display-mode: standalone)').matches ||
        window.navigator.standalone === true
      );
    },
    isIOS: function () {
      return /iphone|ipad|ipod/i.test(window.navigator.userAgent);
    },
    canInstall: function () {
      return Boolean(deferredPrompt);
    },
    promptInstall: async function () {
      if (!deferredPrompt) return null;
      deferredPrompt.prompt();
      const choice = await deferredPrompt.userChoice;
      deferredPrompt = null;
      return choice ? choice.outcome : null;
    },
  };
})();
