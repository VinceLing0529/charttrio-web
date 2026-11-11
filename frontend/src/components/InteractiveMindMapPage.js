import React, { useState, useEffect, useCallback } from 'react';
import { useParams } from 'react-router-dom';
import ReportShell from './ReportShell';
import { fetchModuleContent } from '../utils/moduleContent';

const BRANCHES = [
    { key: 'positive_traits', title: 'Strengths of Character', accent: 'border-secondary-600', chip: 'bg-secondary-600' },
    { key: 'negative_tendencies', title: 'Tricky Tendencies', accent: 'border-primary-600', chip: 'bg-primary-600' },
    { key: 'conflicting_aspects', title: 'Inner Conflicts', accent: 'border-accent-500', chip: 'bg-accent-500' },
    { key: 'strength_areas', title: 'Areas That Flourish', accent: 'border-primary-800', chip: 'bg-primary-800' },
    { key: 'weakness_areas', title: 'Areas to Watch', accent: 'border-ink-soft', chip: 'bg-ink-soft' }
];

export default function InteractiveMindMapPage() {
    const { orderId } = useParams();
    const [aiData, setAiData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    const load = useCallback(async () => {
        try {
            setLoading(true);
            setError(null);
            const parsed = await fetchModuleContent(orderId, 'mindmap');
            setAiData(parsed);
        } catch (err) {
            setError('Could not load the personality map. Please try again shortly.');
        } finally {
            setLoading(false);
        }
    }, [orderId]);

    useEffect(() => { load(); }, [load]);

    return (
        <ReportShell orderId={orderId} title="Personality Panorama · Mind Map" subtitle="Your chart structure and life themes, in five dimensions" loading={loading} error={error} onRetry={load}>
            {aiData && (
                <div className="space-y-6">
                    <div className="text-center py-4">
                        <h2 className="text-2xl font-serif font-black text-ink">Your Personality at a Glance</h2>
                        <p className="text-ink-faint text-sm mt-2">Your personality structure, cross-checked across BaZi, Zi Wei and Vedic astrology</p>
                    </div>
                    {BRANCHES.map((branch) => {
                        const data = aiData[branch.key];
                        if (!data?.overview) return null;
                        return (
                            <article key={branch.key} className={`rounded-2xl border border-line border-l-4 ${branch.accent} bg-paper-card p-6 md:p-8`}>
                                <h3 className="text-xl font-serif font-bold text-ink mb-3">{branch.title}</h3>
                                <p className="text-ink-soft leading-loose mb-6">{data.overview}</p>
                                {data.plain_summary && (
                                    <div className="rounded-xl bg-secondary-50 border border-secondary-200 px-4 py-3 mb-6">
                                        <p className="text-sm font-serif font-bold text-secondary-700 mb-1">In Plain Words</p>
                                        <p className="text-ink leading-relaxed">{data.plain_summary}</p>
                                    </div>
                                )}
                                {Array.isArray(data.details) && data.details.length > 0 && (
                                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                                        {data.details.map((detail, idx) => (
                                            <div key={idx} className="flex gap-3 rounded-xl bg-paper p-4 border border-line">
                                                <span className={`flex-shrink-0 h-fit px-2.5 py-1 rounded text-paper-card text-sm font-serif font-bold ${branch.chip}`}>
                                                    {detail.title}
                                                </span>
                                                <p className="text-sm text-ink-soft leading-relaxed">{detail.description}</p>
                                            </div>
                                        ))}
                                    </div>
                                )}
                            </article>
                        );
                    })}
                </div>
            )}
        </ReportShell>
    );
}
