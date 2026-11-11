import React from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowLeft, Clock } from 'lucide-react';

// 付费报告四个详情页共用的纸面外壳：与 FinalReport / ResultsPage 同一套宣纸设计。
export default function ReportShell({ orderId, title, subtitle, loading, error, onRetry, children }) {
    const navigate = useNavigate();
    return (
        <div className="min-h-screen bg-paper relative">
            <div className="relative z-10 flex items-center justify-between p-6 bg-paper-card border-b border-line">
                <div className="flex items-center gap-4">
                    <button
                        onClick={() => navigate(`/final-report/${orderId}`)}
                        className="p-2 rounded bg-paper-deep hover:bg-line transition-colors"
                    >
                        <ArrowLeft className="w-5 h-5 text-ink-soft" />
                    </button>
                    <div>
                        <h1 className="text-xl font-serif font-bold text-ink">{title}</h1>
                        <p className="text-ink-faint text-sm">Order: {orderId}{subtitle ? ` | ${subtitle}` : ''}</p>
                    </div>
                </div>
            </div>
            <div className="relative z-10 max-w-5xl mx-auto p-6">
                {loading ? (
                    <div className="flex flex-col items-center justify-center py-24">
                        <Clock className="w-8 h-8 text-primary-600 animate-spin mb-4" />
                        <p className="text-ink-soft">Loading your report...</p>
                    </div>
                ) : error ? (
                    <div className="text-center py-24">
                        <p className="text-primary-700 mb-4">{error}</p>
                        <div className="flex gap-3 justify-center">
                            {onRetry && (
                                <button onClick={onRetry} className="px-4 py-2 bg-primary-600 text-paper-card rounded hover:bg-primary-700 transition-colors">
                                    Retry
                                </button>
                            )}
                            <button
                                onClick={() => navigate(`/final-report/${orderId}`)}
                                className="px-4 py-2 bg-paper-card border border-line text-ink-soft rounded hover:border-accent-300 transition-colors"
                            >
                                Back to Report Index
                            </button>
                        </div>
                    </div>
                ) : (
                    <>
                        {children}
                        <p className="text-center text-xs text-ink-faint mt-10 pb-4">
                            This report is generated from traditional astrology models, for reflection only. For major decisions — investing, marriage, changing jobs — please weigh it against real-world conditions.
                        </p>
                    </>
                )}
            </div>
        </div>
    );
}
