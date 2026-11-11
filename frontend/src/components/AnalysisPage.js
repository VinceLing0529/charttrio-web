import React, { useState, useEffect, useCallback } from 'react';
import { useParams } from 'react-router-dom';
import ReportShell from './ReportShell';
import { fetchModuleContent } from '../utils/moduleContent';

const SECTION_ORDER = ['summary', 'talents', 'tensions', 'blindspots', 'guidance'];

export default function AnalysisPage() {
    const { orderId } = useParams();
    const [aiData, setAiData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    const load = useCallback(async () => {
        try {
            setLoading(true);
            setError(null);
            const parsed = await fetchModuleContent(orderId, 'analysis');
            setAiData(parsed);
        } catch (err) {
            setError('Could not load the in-depth analysis. Please try again shortly.');
        } finally {
            setLoading(false);
        }
    }, [orderId]);

    useEffect(() => { load(); }, [load]);

    const sections = aiData
        ? SECTION_ORDER.filter((key) => aiData[key]?.overview).map((key) => ({
            key,
            title: aiData[key].title || key,
            overview: aiData[key].overview,
            plainSummary: aiData[key].plain_summary || ''
        }))
        : [];

    return (
        <ReportShell orderId={orderId} title="In-Depth Analysis · Strengths & Blind Spots" subtitle="Three charts, cross-checked" loading={loading} error={error} onRetry={load}>
            {sections.length === 0 ? (
                <p className="text-center text-ink-faint py-16">This module is not available yet.</p>
            ) : (
                <div className="space-y-6">
                    {sections.map((section, idx) => (
                        <article
                            key={section.key}
                            className={`rounded-2xl border p-6 md:p-8 ${idx === 0 ? 'bg-paper-card border-accent-300' : 'bg-paper-card border-line'}`}
                        >
                            <div className="flex items-baseline gap-3 mb-4">
                                <span className="font-serif text-accent-500 text-lg">{['壹', '贰', '叁', '肆', '伍'][idx] || idx + 1}</span>
                                <h2 className="text-xl md:text-2xl font-serif font-bold text-ink">{section.title}</h2>
                            </div>
                            <p className="text-ink-soft leading-loose whitespace-pre-line">{section.overview}</p>
                            {section.plainSummary && (
                                <div className="mt-6 rounded-xl bg-secondary-50 border border-secondary-200 px-5 py-4">
                                    <p className="text-sm font-serif font-bold text-secondary-700 mb-1.5">In Plain Words</p>
                                    <p className="text-ink leading-relaxed">{section.plainSummary}</p>
                                </div>
                            )}
                        </article>
                    ))}
                    <p className="text-center text-ink-faint text-sm pt-2">For reflection only — for major decisions, weigh this against real-world conditions.</p>
                </div>
            )}
        </ReportShell>
    );
}
