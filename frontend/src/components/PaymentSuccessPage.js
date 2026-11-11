import React, { useEffect, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import toast from 'react-hot-toast';
import { API_BASE } from '../config';

// Stripe 支付成功回跳页：凭 session_id 向后端取已付费的码（后端核验付款后发放）。
// 正常路径不再要求用户输码：码暂存 localStorage，自动跳回结果页直达报告生成；
// 码同时以“恢复码”形式展示，作为换设备/自动跳转失败时的兜底。
function PaymentSuccessPage() {
    const [params] = useSearchParams();
    const sessionId = params.get('session_id') || '';
    const [state, setState] = useState({ status: 'checking', code: null, hasChart: false });

    useEffect(() => {
        if (!sessionId) { setState({ status: 'missing', code: null, hasChart: false }); return; }
        let tries = 0;
        let timer = null;
        const poll = async () => {
            tries += 1;
            try {
                const r = await fetch(`${API_BASE}/api/payments/stripe/session/${sessionId}`);
                const d = await r.json();
                if (d.code) {
                    let hasChart = false;
                    try {
                        localStorage.setItem('li_paid_code', d.code);
                        hasChart = !!localStorage.getItem('li_last_chart');
                    } catch { /* 存储不可用时走手动兜底 */ }
                    setState({ status: 'paid', code: d.code, hasChart });
                    return;
                }
                if (d.status === 'paid') { setState({ status: 'paid', code: null, hasChart: false }); return; }
            } catch (e) { /* 网络抖动时继续轮询 */ }
            if (tries < 15) { timer = setTimeout(poll, 2000); }
            else { setState({ status: 'timeout', code: null, hasChart: false }); }
        };
        poll();
        return () => { if (timer) clearTimeout(timer); }
    }, [sessionId]);

    // 同浏览器有排盘记录时自动直达结果页（结果页会核销并开始生成报告）
    useEffect(() => {
        if (state.status === 'paid' && state.code && state.hasChart) {
            const t = setTimeout(() => { window.location.href = '/results'; }, 1500);
            return () => clearTimeout(t);
        }
    }, [state]);

    const copyCode = async () => {
        try { await navigator.clipboard.writeText(state.code); toast.success('Recovery code copied'); }
        catch (e) { toast.error('Copy failed — please copy it manually'); }
    };

    return (
        <div className="min-h-[60vh] flex items-center justify-center px-4 py-16">
            <div className="bg-paper-card border border-line rounded shadow-xl p-8 w-[28rem] max-w-[92vw] text-center">
                <h2 className="text-2xl font-serif font-bold text-ink mb-4 tracking-widest">Payment Result</h2>
                {state.status === 'checking' && <p className="text-ink-soft">Confirming your payment…</p>}
                {state.status === 'paid' && state.code && state.hasChart && (
                    <>
                        <p className="text-ink-soft mb-3">Payment successful! Opening your full report — nothing more to do…</p>
                        <button onClick={() => { window.location.href = '/results'; }} className="w-full bg-primary-600 hover:bg-primary-700 text-paper-card py-3 rounded mb-3 transition-colors font-medium">Open My Report</button>
                        <p className="text-xs text-ink-faint">If the redirect fails, here is your recovery code: <span className="font-mono font-bold text-primary-600">{state.code}</span>(On the results page, tap "Get My Full Report" and enter it. Single use only.)</p>
                    </>
                )}
                {state.status === 'paid' && state.code && !state.hasChart && (
                    <>
                        <p className="text-ink-soft mb-3">Payment successful! This is your report recovery code — keep it safe:</p>
                        <p className="text-2xl font-mono font-bold text-primary-600 tracking-widest mb-4">{state.code}</p>
                        <button onClick={copyCode} className="w-full bg-primary-600 hover:bg-primary-700 text-paper-card py-3 rounded mb-3 transition-colors font-medium">Copy Recovery Code</button>
                        <p className="text-xs text-ink-faint mb-4">We could not find a chart on this device (you may have cast it on another one). On the device with your chart, open the results page, tap "Get My Full Report" and enter the recovery code. Single use only.</p>
                    </>
                )}
                {state.status === 'paid' && !state.code && <p className="text-ink-soft">Payment confirmed — your report is being unlocked. Please refresh this page in a moment.</p>}
                {state.status === 'timeout' && <p className="text-ink-soft">Verification timed out. If you completed payment, your report will unlock automatically once the payment is confirmed — please reopen this page shortly. Still stuck? Contact support with your payment record.</p>}
                {state.status === 'missing' && <p className="text-ink-soft">Payment session details are missing, so we cannot verify this payment.</p>}
                <Link to="/" className="inline-block mt-2 text-primary-600 underline">Back to Home</Link>
            </div>
        </div>
    );
}

export default PaymentSuccessPage;
