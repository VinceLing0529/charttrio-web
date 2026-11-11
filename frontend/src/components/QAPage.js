import React, { useState, useEffect, useCallback } from 'react';
import { useParams } from 'react-router-dom';
import { ChevronDown } from 'lucide-react';
import ReportShell from './ReportShell';
import { fetchModuleContent } from '../utils/moduleContent';

// 分类与顺序以付费 QA 模块的数据为准（问题文本也来自数据本身，不在前端写死，
// 避免与后端固定问题集漂移导致问答错位）。
const CATEGORIES = [
    { key: 'wealth_questions', label: 'Money' },
    { key: 'career_questions', label: 'Career' },
    { key: 'love_questions', label: 'Love' },
    { key: 'personality_questions', label: 'Personality' },
    { key: 'fortune_questions', label: 'Timing' }
];

export default function QAPage() {
    const { orderId } = useParams();
    const [aiData, setAiData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [openKey, setOpenKey] = useState(null);

    const load = useCallback(async () => {
        try {
            setLoading(true);
            setError(null);
            const parsed = await fetchModuleContent(orderId, 'qa');
            setAiData(parsed);
        } catch (err) {
            setError('Could not load the Q&A. Please try again shortly.');
        } finally {
            setLoading(false);
        }
    }, [orderId]);

    useEffect(() => { load(); }, [load]);

    return (
        <ReportShell orderId={orderId} title="Your Questions · 30 Answered" subtitle="Money / Career / Love / Personality / Timing" loading={loading} error={error} onRetry={load}>
            {aiData && (
                <div className="space-y-8">
                    {CATEGORIES.map((cat) => {
                        const items = Array.isArray(aiData[cat.key]) ? aiData[cat.key] : [];
                        if (items.length === 0) return null;
                        return (
                            <section key={cat.key} className="rounded-2xl border border-line bg-paper-card p-6 md:p-8">
                                <div className="flex items-baseline gap-3 mb-5">
                                    <h2 className="text-xl font-serif font-bold text-ink">{cat.label}</h2>
                                    <span className="text-sm text-ink-faint">{items.length} questions</span>
                                </div>
                                <div className="divide-y divide-line">
                                    {items.map((item, idx) => {
                                        const itemKey = `${cat.key}-${idx}`;
                                        const open = openKey === itemKey;
                                        return (
                                            <div key={itemKey}>
                                                <button
                                                    onClick={() => setOpenKey(open ? null : itemKey)}
                                                    className="w-full flex items-center justify-between gap-4 py-4 text-left"
                                                >
                                                    <span className="text-ink font-medium">{item.question}</span>
                                                    <ChevronDown className={`w-4 h-4 text-ink-faint flex-shrink-0 transition-transform ${open ? 'rotate-180' : ''}`} />
                                                </button>
                                                {open && (
                                                    <p className="pb-5 text-ink-soft leading-loose whitespace-pre-line">{item.answer}</p>
                                                )}
                                            </div>
                                        );
                                    })}
                                </div>
                            </section>
                        );
                    })}
                    <p className="text-center text-ink-faint text-sm">For major decisions — investing, marriage, changing jobs — treat this as reflection only and weigh it against real-world conditions.</p>
                </div>
            )}
        </ReportShell>
    );
}
