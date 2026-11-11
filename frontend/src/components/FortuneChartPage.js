import React, { useState, useEffect, useCallback } from 'react';
import { useParams } from 'react-router-dom';
import ReportShell from './ReportShell';
import { fetchModuleContent } from '../utils/moduleContent';

const DIMENSIONS = [
    { key: 'career_score', label: 'Career', bar: 'bg-primary-600' },
    { key: 'wealth_score', label: 'Money', bar: 'bg-accent-500' },
    { key: 'relationship_score', label: 'Love', bar: 'bg-secondary-600' },
    { key: 'health_score', label: 'Energy', bar: 'bg-primary-800' }
];

const avg = (p) => DIMENSIONS.reduce((sum, d) => sum + (Number(p[d.key]) || 0), 0) / DIMENSIONS.length;

export default function FortuneChartPage() {
    const { orderId } = useParams();
    const [months, setMonths] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    const load = useCallback(async () => {
        try {
            setLoading(true);
            setError(null);
            const parsed = await fetchModuleContent(orderId, 'fortune');
            if (!Array.isArray(parsed.monthly_predictions) || parsed.monthly_predictions.length === 0) {
                throw new Error('empty');
            }
            setMonths(parsed.monthly_predictions);
        } catch (err) {
            setError('Could not load your forecast. Please try again shortly.');
        } finally {
            setLoading(false);
        }
    }, [orderId]);

    useEffect(() => { load(); }, [load]);

    const best = months ? months.reduce((a, b) => (avg(b) > avg(a) ? b : a)) : null;
    const lowest = months ? months.reduce((a, b) => (avg(b) < avg(a) ? b : a)) : null;

    return (
        <ReportShell orderId={orderId} title="Your Forecast · The Next 12 Months" subtitle="Four scores measured against your own baseline (5 = your normal)" loading={loading} error={error} onRetry={load}>
            {months && (
                <div className="space-y-6">
                    <div className="rounded-2xl border border-line bg-paper-card p-6">
                        <h2 className="font-serif font-bold text-ink text-lg mb-2">Your Year at a Glance</h2>
                        <p className="text-ink-soft leading-relaxed">
                            Your peak lands in <span className="text-primary-700 font-medium">{best.month}</span>(overall {avg(best).toFixed(1)}),
                            and the month to take most gently is <span className="text-primary-700 font-medium">{lowest.month}</span>(overall {avg(lowest).toFixed(1)}),
                            Scores are relative to your own cycles, not absolute good or bad luck: read the rhythm of the year first, then each month in detail.
                        </p>
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                        {months.map((p, idx) => (
                            <article key={idx} className="rounded-2xl border border-line bg-paper-card p-6">
                                <div className="flex items-baseline justify-between mb-4">
                                    <h3 className="font-serif font-bold text-ink text-lg">{p.month}</h3>
                                    <span className="text-sm text-ink-faint">Overall <span className="text-ink font-semibold">{avg(p).toFixed(1)}</span></span>
                                </div>
                                <div className="space-y-2.5">
                                    {DIMENSIONS.map((d) => (
                                        <div key={d.key} className="flex items-center gap-3">
                                            <span className="text-sm text-ink-soft w-10">{d.label}</span>
                                            <div className="flex-1 h-2 rounded-full bg-paper-deep overflow-hidden">
                                                <div className={`h-full ${d.bar} rounded-full`} style={{ width: `${(Number(p[d.key]) || 0) * 10}%` }} />
                                            </div>
                                            <span className="text-sm text-ink w-6 text-right">{p[d.key]}</span>
                                        </div>
                                    ))}
                                </div>
                                {p.analysis && <p className="mt-4 text-sm text-ink-soft leading-relaxed">{p.analysis}</p>}
                            </article>
                        ))}
                    </div>
                    <p className="text-center text-ink-faint text-sm">The energy score speaks only to stamina and stress levels, never to illness. For major decisions, weigh this against real-world conditions.</p>
                </div>
            )}
        </ReportShell>
    );
}
