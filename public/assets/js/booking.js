/* Cal.com Inline Embed integration. Booking and free-slot validation live on Cal.com. */
(() => {
  'use strict';

  const slot = document.getElementById('cal-inline');
  const status = document.getElementById('booking-status');
  const external = document.getElementById('booking-open-link');
  if (!slot || !status || !external) return;

  function setStatus(message, error = false) {
    status.hidden = false;
    status.textContent = message;
    status.classList.toggle('booking__status--error', error);
  }

  function parseEventUrl(raw) {
    if (typeof raw !== 'string' || !raw.trim()) return null;
    let url;
    try {
      url = new URL(raw.trim());
    } catch {
      return null;
    }
    if (url.protocol !== 'https:' || url.username || url.password || url.port) return null;
    const isEU = ['cal.eu', 'app.cal.eu'].includes(url.hostname);
    const isGlobal = ['cal.com', 'app.cal.com'].includes(url.hostname);
    if (!isEU && !isGlobal) return null;
    const segments = url.pathname.split('/').filter(Boolean);
    // A single-user event typically uses /username/event-slug.
    if (segments.length < 2 || segments.length > 3 || segments.some(part => !/^[a-zA-Z0-9_-]+$/.test(part))) return null;
    const origin = isEU ? 'https://app.cal.eu' : 'https://app.cal.com';
    return {
      calLink: segments.join('/'),
      origin,
      publicUrl: `${url.origin}/${segments.join('/')}`,
      scriptUrl: `${origin}/embed/embed.js`,
    };
  }

  const config = window.KTAWF_BOOKING || {};
  if (!config.eventUrl) {
    // The site must not show fake availability or send bookings to a sample account.
    setStatus('Онлайн-запис ще не активовано. Для узгодження часу скористайтеся контактами нижче.');
    return;
  }

  const booking = parseEventUrl(config.eventUrl);
  if (!booking) {
    setStatus('Онлайн-запис тимчасово недоступний. Скористайтеся контактами нижче.', true);
    return;
  }

  external.href = booking.publicUrl;
  external.hidden = false;
  setStatus('Завантаження календаря вільних дат і часу…');

  const brandColor = /^#[\da-fA-F]{6}$/.test(config.brandColor || '') ? config.brandColor : '#25382e';
  const theme = config.theme === 'dark' ? 'dark' : 'light';
  let hasEmbed = false;

  const onEmbedMissing = () => {
    if (!hasEmbed) {
      setStatus('Не вдалося завантажити календар. Спробуйте відкрити запис за посиланням нижче.', true);
    }
  };

  // Official Cal.com embed loader with asynchronous command queue.
  // Cal.com owns all scheduling state and the booking form.
  (function installCalBootstrap(win, scriptUrl) {
    if (typeof win.Cal === 'function') return;
    const enqueue = (api, args) => api.q.push(args);
    win.Cal = function () {
      const cal = win.Cal;
      const args = arguments;
      if (!cal.loaded) {
        cal.ns = {};
        cal.q = cal.q || [];
        const script = document.createElement('script');
        script.async = true;
        script.src = scriptUrl;
        script.referrerPolicy = 'strict-origin-when-cross-origin';
        script.addEventListener('error', onEmbedMissing, { once: true });
        document.head.appendChild(script);
        cal.loaded = true;
      }
      if (args[0] === 'init') {
        const namespace = args[1];
        if (typeof namespace === 'string') {
          const ns = function () { enqueue(ns, arguments); };
          ns.q = ns.q || [];
          cal.ns[namespace] = cal.ns[namespace] || ns;
          enqueue(cal.ns[namespace], args);
          enqueue(cal, ['initNamespace', namespace]);
        } else {
          enqueue(cal, args);
        }
        return;
      }
      enqueue(cal, args);
    };
  })(window, booking.scriptUrl);

  // Watch only the expected embed mount, not document-wide changes.
  const observer = new MutationObserver(() => {
    if (slot.querySelector('iframe')) {
      hasEmbed = true;
      status.hidden = true;
      observer.disconnect();
    }
  });
  observer.observe(slot, { childList: true, subtree: true });

  try {
    window.Cal('init', { origin: booking.origin });
    window.Cal('inline', {
      elementOrSelector: '#cal-inline',
      calLink: booking.calLink,
      config: { layout: 'month_view', theme },
    });
    window.Cal('ui', {
      theme,
      styles: { branding: { brandColor } },
      hideEventTypeDetails: false,
      layout: 'month_view',
    });
  } catch (error) {
    observer.disconnect();
    setStatus('Не вдалося запустити форму запису. Скористайтеся прямим посиланням нижче.', true);
    return;
  }

  // Keep direct booking link visible even if the third-party script is blocked.
  window.setTimeout(() => {
    if (!hasEmbed) onEmbedMissing();
    // Keep observing: a slow iframe can still appear and clear the warning later.
  }, 15000);
})();
