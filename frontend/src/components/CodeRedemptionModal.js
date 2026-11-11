import React, { useEffect, useState } from 'react';
import toast from 'react-hot-toast';
import { API_BASE } from '../config';
import { trackInitiateCheckout } from '../utils/metaPixel';

function CodeRedemptionModal({ isOpen, onClose }) {
    const [stripeEnabled, setStripeEnabled] = useState(false);
    const [paying, setPaying] = useState(false);

    useEffect(() => {
        if (!isOpen) return;
        fetch(`${API_BASE}/api/payments/config`)
            .then(r => r.ok ? r.json() : null)
            .then(d => setStripeEnabled(!!(d && d.stripe_enabled)))
            .catch(() => setStripeEnabled(false));
    }, [isOpen]);

    const handleOnlinePay = async () => {
        setPaying(true);
        try {
            const response = await fetch(`${API_BASE}/api/payments/stripe/checkout`, { method: 'POST' });
            if (!response.ok) throw new Error('checkout failed');
            const data = await response.json();
            // Meta Pixel: user committed to pay and a Checkout session now exists.
            trackInitiateCheckout();
            window.location.href = data.url;
        } catch (error) {
            console.error('在线支付发起失败:', error);
            toast.error('Online payment is temporarily unavailable — please try again shortly');
            setPaying(false);
        }
    };

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 bg-ink/50 flex items-center justify-center z-50">
            <div className="bg-paper-card border border-line rounded shadow-2xl p-6 w-96 max-w-[90vw]">
                <h3 className="text-xl font-serif font-bold text-ink mb-4 text-center tracking-widest">Get the Full Report</h3>

                <p className="text-center text-ink-soft text-sm mb-4">
                    Full report <span className="text-lg font-bold text-primary-600">$24.90</span> (includes your 12-month forecast and the 30-question Q&A)
                </p>

                <p className="text-sm text-ink-soft mb-4">
                    Pay online below with your card. Your report unlocks automatically right after payment — no codes to type, ever.
                </p>

                {stripeEnabled ? (
                    <button
                        onClick={handleOnlinePay}
                        disabled={paying}
                        className="w-full bg-primary-600 hover:bg-primary-700 text-paper-card py-3 rounded mb-3 disabled:opacity-50 transition-colors font-medium"
                    >
                        {paying ? 'Taking you to checkout...' : 'Pay $24.90 by Card'}
                    </button>
                ) : (
                    <p className="text-center text-sm text-ink-faint border border-line rounded py-3 mb-3">
                        Checkout is briefly unavailable — please try again shortly
                    </p>
                )}

                <p className="text-xs text-ink-faint mb-4">
                    Payments are processed securely by Stripe. After paying, your report opens automatically. If you close the page mid-way, come back in the same browser to pick up where you left off.
                </p>

                <button
                    onClick={onClose}
                    className="w-full bg-paper-deep hover:bg-line text-ink-soft py-2 rounded transition-colors"
                >
                    Cancel
                </button>
            </div>
        </div>
    );
}

export default CodeRedemptionModal;
