import React, { useState, useEffect } from 'react';
import { API_BASE } from '../config';
import { useParams, useNavigate } from 'react-router-dom';
import { Clock, CheckCircle, ArrowLeft, Camera } from 'lucide-react';

export default function FinalReport() {
    const { orderId } = useParams();
    const navigate = useNavigate();
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [moduleStatus, setModuleStatus] = useState({});
    const [generatingModule, setGeneratingModule] = useState(null);
    const [reportData, setReportData] = useState(null);
    const [snapshotUrl, setSnapshotUrl] = useState(null);
    const [snapshotLoading, setSnapshotLoading] = useState(false);
    const [snapshotError, setSnapshotError] = useState(null);
    // 注意：后端模块进度只有 0 / 100 两个真实值（见 /api/ai-report/module-status，
    // 服务端一次调用 AI 并返回结果，等待期间没有中间进度）。此前前端曾用
    // 每秒 +10% 的定时器伪造 0→90% 的进度条，2026-11-01 包6 已删除：
    // 生成中只显示“正在生成…”状态，不再显示任何估算百分比。
    const pollTimers = React.useRef({});

    useEffect(() => {
        loadModuleStatus();
        loadReportData();
    }, [orderId]);

    const loadModuleStatus = async () => {
        try {
            const response = await fetch(`${API_BASE}/api/ai-report/module-status/${orderId}`);
            if (response.ok) {
                const statusData = await response.json();
                console.log('模块状态数据:', statusData);

                // 将后端状态格式转换为前端期望的格式
                const moduleProgress = {};
                if (statusData.modules) {
                    Object.keys(statusData.modules).forEach(moduleName => {
                        const moduleStatus = statusData.modules[moduleName];
                        moduleProgress[moduleName] = moduleStatus.progress || 0;
                    });
                }

                setModuleStatus(moduleProgress);
            }
        } catch (err) {
            console.error('加载模块状态失败:', err);
        }
    };

    const handleGenerateModule = async (moduleName) => {
        if (generatingModule) return;
        setGeneratingModule(moduleName);
        // 只轮询后端真实状态（0 未开始 / 100 已完成），不做前端估算动画。
        pollTimers.current[moduleName] = setInterval(async () => {
            const resp = await fetch(`${API_BASE}/api/ai-report/module-status/${orderId}`);
            if (resp.ok) {
                const statusData = await resp.json();
                const backendProgress = statusData.modules?.[moduleName]?.progress || 0;
                if (backendProgress >= 100) {
                    clearInterval(pollTimers.current[moduleName]);
                    setGeneratingModule(null);
                    loadModuleStatus();
                }
            }
        }, 1000);
        // 实际请求后端
        try {
            await fetch(`${API_BASE}/api/ai-report/generate-module`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ order_id: orderId, module: moduleName })
            });
        } catch (err) {
            clearInterval(pollTimers.current[moduleName]);
            setGeneratingModule(null);
            setError('Module generation failed');
        }
    };

    const loadReportData = async () => {
        try {
            setLoading(true);
            const response = await fetch(`${API_BASE}/api/ai-report/report/${orderId}`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                }
            });

            if (!response.ok) {
                if (response.status === 404) {
                    throw new Error('Report not found — please check your order ID');
                } else {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
            }

            const data = await response.json();
            console.log('加载的报告数据:', data);

            // 将后端数据结构映射到前端期望的格式
            const mappedData = {
                sections: data.sections || [],
                order_id: data.order_id,
                generated_at: data.generated_at
            };

            setReportData(mappedData);
        } catch (err) {
            console.error('加载报告失败:', err);
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    const handleBack = () => {
        navigate('/');
    };

    // 命盘快照：向后端取一张渲染好的 PNG（内容来自本报告的大白话），弹窗预览 + 保存
    const handleSnapshot = async () => {
        if (snapshotLoading) return;
        setSnapshotLoading(true);
        setSnapshotError(null);
        try {
            const resp = await fetch(`${API_BASE}/api/ai-report/snapshot/${orderId}`);
            if (!resp.ok) {
                let msg = 'Snapshot failed — please try again in a moment';
                try { const j = await resp.json(); if (j && j.detail) msg = j.detail; } catch (e) { /* 非 JSON 错误体 */ }
                throw new Error(msg);
            }
            const blob = await resp.blob();
            setSnapshotUrl(URL.createObjectURL(blob));
        } catch (err) {
            setSnapshotError(err.message);
        } finally {
            setSnapshotLoading(false);
        }
    };

    const closeSnapshot = () => {
        if (snapshotUrl) URL.revokeObjectURL(snapshotUrl);
        setSnapshotUrl(null);
    };

    const handleCardClick = (section) => {
        // 导航到独立的页面
        switch (section.id) {
            case 'mindmap':
                navigate(`/final-report/${orderId}/interactive-mind-map`);
                break;
            case 'fortune':
                navigate(`/final-report/${orderId}/fortune-chart`);
                break;
            case 'qa':
                navigate(`/final-report/${orderId}/qa`);
                break;
            case 'analysis':
                navigate(`/final-report/${orderId}/analysis`);
                break;
            default:
                console.log('未知的section:', section.id);
        }
    };

    const getStatusIcon = (progress, isGenerating) => {
        if (progress >= 100) {
            return <CheckCircle className="w-5 h-5 text-green-400" />;
        } else if (isGenerating) {
            return <Clock className="w-5 h-5 text-primary-600 animate-spin" />;
        } else {
            return <Clock className="w-5 h-5 text-ink-faint" />;
        }
    };

    const getStatusText = (progress, isGenerating) => {
        if (progress >= 100) return "Done";
        if (isGenerating) return "Generating…";
        return "Not started";
    };

    // 固定的示例数据，直接使用ExamplePage的内容
    const reportSections = [
        {
            id: "analysis",
            title: "Strengths & Blind Spots",
            description: "Your three charts read together — where you shine, where you trip, and why.",
            icon: "析",
            gradient: "bg-primary-600",
            bgGradient: "bg-primary-50",
            borderGradient: "border-primary-300"
        },
        {
            id: "mindmap",
            title: "Personality Map",
            description: "Your personality structure and life themes, mapped out.",
            icon: "图",
            gradient: "bg-accent-500",
            bgGradient: "bg-accent-50",
            borderGradient: "border-accent-300"
        },
        {
            id: "fortune",
            title: "Your Next 12 Months",
            description: "A month-by-month look at the year ahead, based on your cycles.",
            icon: "运",
            gradient: "bg-secondary-600",
            bgGradient: "bg-secondary-50",
            borderGradient: "border-secondary-300"
        },
        {
            id: "qa",
            title: "30 Questions, Answered",
            description: "Thirty core questions across five areas of life, answered from your charts.",
            icon: "答",
            gradient: "bg-primary-800",
            bgGradient: "bg-primary-50",
            borderGradient: "border-primary-200"
        }
    ];

    // 加载状态
    if (loading) {
        return (
            <div className="min-h-screen bg-paper flex items-center justify-center">
                <div className="text-center">
                    <Clock className="w-8 h-8 text-primary-600 animate-spin mx-auto mb-4" />
                    <p className="text-ink-soft">Loading your report...</p>
                </div>
            </div>
        );
    }

    // 错误状态
    if (error) {
        return (
            <div className="min-h-screen bg-paper flex items-center justify-center">
                <div className="text-center">
                    <p className="text-primary-700 mb-4">{/failed to fetch|network/i.test(error || '') ? 'Network error — please check your connection and try again.' : error}</p>
                    <div className="flex gap-3 justify-center">
                        <button
                            onClick={() => { setError(null); loadReportData(); }}
                            className="px-4 py-2 bg-primary-600 text-paper-card rounded hover:bg-primary-700 transition-colors"
                        >
                            Retry
                        </button>
                        <button
                            onClick={handleBack}
                            className="px-4 py-2 bg-paper-card border border-line text-ink-soft rounded hover:border-accent-300 transition-colors"
                        >
                            Back to Home
                        </button>
                    </div>
                </div>
            </div>
        );
    }

    // 主页面 - 使用ExamplePage的完整样式
    return (
        <div className="min-h-screen bg-paper relative">

            {/* Header */}
            <div className="relative z-10 flex items-center justify-between p-6 bg-paper-card border-b border-line">
                <div className="flex items-center gap-4">
                    <button
                        onClick={handleBack}
                        className="p-2 rounded bg-paper-deep hover:bg-line transition-colors"
                    >
                        <ArrowLeft className="w-5 h-5 text-ink-soft" />
                    </button>
                    <div>
                        <h1 className="text-xl font-serif font-bold text-ink">Your ChartTrio Report</h1>
                        <p className="text-ink-faint text-sm">Order: {orderId}</p>
                    </div>
                </div>

                {/* Overall Progress：只统计已完成模块数（每模块 25%），不是单个模块的实时进度 */}
                <div className="flex items-center gap-3">
                    <div className="text-right">
                        <p className="text-sm text-ink-faint">Overall progress (modules completed of 4)</p>
                        <p className="text-lg font-semibold text-ink">
                            {Math.round(Object.values(moduleStatus).reduce((sum, val) => sum + (val || 0), 0) / 4)}%
                        </p>
                    </div>
                    <div className="w-24 bg-paper-deep rounded-full h-2">
                        <div
                            className="bg-primary-600 h-2 rounded-full transition-all duration-500"
                            style={{
                                width: `${Object.values(moduleStatus).reduce((sum, val) => sum + (val || 0), 0) / 4}%`
                            }}
                        ></div>
                    </div>
                </div>
            </div>

            {/* Main Content */}
            <div className="relative z-10 max-w-6xl mx-auto p-6">
                {orderId === 'LIFEDEMO1995' && (
                    <div className="mb-6 rounded-2xl border border-accent-300 bg-accent-50 p-4 text-center">
                        <p className="text-ink font-serif font-bold">Sample Report · The real thing, from the paid edition</p>
                        <p className="text-ink-soft text-sm mt-1">Sample chart: female, born August 15, 1995, 9:30 AM, Beijing. All four modules are shown in full — exactly what paying customers receive (the current version also weaves in luck cycles and yearly rhythms).</p>
                        <button onClick={() => navigate('/')} className="mt-3 px-5 py-2 bg-primary-600 text-paper-card rounded-lg hover:bg-primary-700 transition-colors text-sm font-medium">
                            Cast my chart and unlock my report →
                        </button>
                    </div>
                )}
                <div className={`transition-all duration-500 opacity-100 translate-y-0`}>
                    {/* Welcome Section */}
                    <div className="text-center mb-8">
                        <h2 className="text-3xl font-serif font-black text-ink mb-4">Welcome to Your Personal Report</h2>
                        <p className="text-ink-soft text-lg max-w-2xl mx-auto">
                            Built from your birth details, this report reads your life from four angles. Generate each module on its own and explore at your own pace.
                        </p>
                    </div>

                    {/* 命盘快照：优劣分析完成后，可把大白话内容生成一张卡片保存/分享 */}
                    {(moduleStatus.analysis || 0) >= 100 && (
                        <div className="text-center mb-8">
                            <button
                                onClick={handleSnapshot}
                                disabled={snapshotLoading}
                                className="inline-flex items-center gap-2 px-6 py-3 bg-secondary-600 text-paper-card rounded-lg hover:bg-secondary-700 transition-colors font-medium disabled:opacity-60"
                            >
                                <Camera className="w-5 h-5" />
                                {snapshotLoading ? 'Creating your snapshot…' : 'Create a Snapshot Card'}
                            </button>
                            <p className="text-ink-faint text-sm mt-2">Turn the plain-words highlights of your report into a card you can save and share</p>
                            {snapshotError && <p className="text-primary-700 text-sm mt-2">{snapshotError}</p>}
                        </div>
                    )}

                    {/* Report Cards */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
                        {reportSections.map((section) => {
                            // 只用后端真实进度：0 未开始，100 已完成；生成中不显示百分比。
                            const progress = moduleStatus[section.id] || 0;
                            const isGenerating = generatingModule === section.id;

                            return (
                                <div
                                    key={section.id}
                                    className={`relative group cursor-pointer transition-all duration-300 transform hover:scale-105 ${progress >= 100 ? 'hover:shadow-2xl' : ''
                                        }`}
                                    onClick={() => progress >= 100 && handleCardClick(section)}
                                >
                                    {/* Card Background */}
                                    <div className={`absolute inset-0 rounded ${section.bgGradient} opacity-0 group-hover:opacity-100 transition-opacity duration-300`}></div>

                                    {/* Card Content */}
                                    <div className={`relative rounded-2xl p-6 border transition-all duration-300 ${progress >= 100
                                        ? `border ${section.borderGradient} bg-paper-card`
                                        : 'border border-line bg-paper-card'
                                        }`}>
                                        {/* Header */}
                                        <div className="flex items-center justify-between mb-4">
                                            <div className="flex items-center gap-3">
                                                <span className="text-2xl">{section.icon}</span>
                                                <div>
                                                    <h3 className="text-lg font-serif font-bold text-ink">{section.title}</h3>
                                                    <p className="text-ink-faint text-sm">{section.description}</p>
                                                </div>
                                            </div>
                                            <div className="flex items-center gap-2">
                                                {getStatusIcon(progress, isGenerating)}
                                                <span className="text-xs text-ink-faint">{getStatusText(progress, isGenerating)}</span>
                                            </div>
                                        </div>

                                        {/* Status：只有“未开始 / 生成中 / 已完成”三态。
                                            服务端一次返回结果，等待期间没有中间进度，故不显示百分比动画。 */}
                                        <div className="mb-4">
                                            <div className="flex items-center justify-between mb-2">
                                                <span className="text-sm text-ink-faint">Status</span>
                                                <span className="text-sm text-ink">
                                                    {progress >= 100 ? 'Done' : isGenerating ? 'Generating…' : 'Not started'}
                                                </span>
                                            </div>
                                            <div className="w-full bg-paper-deep rounded-full h-2">
                                                <div
                                                    className={`${section.gradient} h-2 rounded-full transition-all duration-500 ${isGenerating ? 'animate-pulse' : ''}`}
                                                    style={{ width: `${progress >= 100 ? 100 : 0}%` }}
                                                ></div>
                                            </div>
                                        </div>

                                        {/* Action Button */}
                                        {progress < 100 ? (
                                            <button
                                                onClick={(e) => {
                                                    e.stopPropagation();
                                                    handleGenerateModule(section.id);
                                                }}
                                                disabled={isGenerating}
                                                className={`w-full py-2 px-4 rounded-lg font-medium transition-all duration-300 ${isGenerating
                                                    ? 'bg-paper-deep text-ink-faint cursor-not-allowed'
                                                    : `${section.gradient} text-paper-card hover:opacity-90`
                                                    }`}
                                            >
                                                {isGenerating ? (
                                                    <div className="flex items-center justify-center gap-2">
                                                        <Clock className="w-4 h-4 animate-spin" />
                                                        Generating...
                                                    </div>
                                                ) : (
                                                    'Generate'
                                                )}
                                            </button>
                                        ) : (
                                            <div className="flex items-center justify-center gap-2 text-secondary-600 text-sm">
                                                <CheckCircle className="w-4 h-4" />
                                                Click to read the full module
                                            </div>
                                        )}
                                    </div>
                                </div>
                            );
                        })}
                    </div>

                    {/* Additional Info */}
                    <div className="text-center text-ink-faint text-sm space-y-1">
                        <p>Once a module is generated, click its card to read it in full</p>
                    </div>
                </div>
            </div>

            {/* 命盘快照预览弹窗 */}
            {snapshotUrl && (
                <div className="fixed inset-0 z-50 bg-black/70 flex items-center justify-center p-4" onClick={closeSnapshot}>
                    <div className="bg-paper-card rounded-2xl p-4 max-w-md w-full max-h-full overflow-y-auto" onClick={(e) => e.stopPropagation()}>
                        <img src={snapshotUrl} alt="Chart snapshot" className="w-full rounded-lg border border-line" />
                        <div className="flex gap-3 mt-4">
                            <a
                                href={snapshotUrl}
                                download={`charttrio-snapshot-${orderId}.png`}
                                className="flex-1 text-center px-4 py-2 bg-primary-600 text-paper-card rounded-lg hover:bg-primary-700 transition-colors font-medium"
                            >
                                Save Image
                            </a>
                            <button
                                onClick={closeSnapshot}
                                className="flex-1 px-4 py-2 bg-paper-card border border-line text-ink-soft rounded-lg hover:border-accent-300 transition-colors"
                            >
                                Close
                            </button>
                        </div>
                        <p className="text-ink-faint text-xs text-center mt-3">On mobile, you can also long-press the image to save it</p>
                    </div>
                </div>
            )}
        </div>
    );
} 