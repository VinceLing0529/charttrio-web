// Meta Pixel event helpers (ChartTrio Website, dataset 29095838006750472).
//
// The base snippet (fbq init + first PageView) lives in public/index.html.
// Every call here is guarded: if fbevents.js is blocked (ad blocker, network,
// privacy mode) or fbq is absent for any reason, these become no-ops and the
// app must never break because of analytics.

export const META_PIXEL_ID = '29095838006750472';
export const REPORT_PRICE_USD = 24.9;
export const REPORT_CURRENCY = 'USD';

function fbqTrack(event, params, options) {
    try {
        if (typeof window !== 'undefined' && typeof window.fbq === 'function') {
            if (options) window.fbq('track', event, params, options);
            else window.fbq('track', event, params);
        }
    } catch (e) {
        /* analytics must never break the app */
    }
}

/** Extra PageView for SPA route changes (the initial one fires from index.html). */
export function trackPageView() {
    fbqTrack('PageView');
}

/** Fired when the user clicked Pay and a Stripe Checkout session was created. */
export function trackInitiateCheckout() {
    fbqTrack('InitiateCheckout', {
        value: REPORT_PRICE_USD,
        currency: REPORT_CURRENCY,
    });
}

// In-page guard against the success page remounting / re-polling in one session.
const firedPurchaseKeys = new Set();

/**
 * Fired once payment is confirmed for an order.
 * `orderKey` is the Stripe checkout session id (unique per purchase); the
 * event is sent at most once per key — a sessionStorage flag survives
 * remounts and page reloads within the browser session, and the key is also
 * sent as Meta's eventID so Meta can dedupe any residual double-fire.
 */
export function trackPurchase(orderKey) {
    if (!orderKey) return;
    if (firedPurchaseKeys.has(orderKey)) return;

    const flagKey = `ct_pixel_purchase_${orderKey}`;
    try {
        if (window.sessionStorage.getItem(flagKey)) {
            firedPurchaseKeys.add(orderKey);
            return;
        }
        window.sessionStorage.setItem(flagKey, '1');
    } catch (e) {
        /* storage unavailable — the in-memory set above still guards remounts */
    }
    firedPurchaseKeys.add(orderKey);

    fbqTrack(
        'Purchase',
        { value: REPORT_PRICE_USD, currency: REPORT_CURRENCY },
        { eventID: orderKey }
    );
}
