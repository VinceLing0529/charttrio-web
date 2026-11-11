import React, { useState, useEffect } from 'react';
import { API_BASE } from '../config';
import { ArrowLeft, Share2, Download, Calendar, Clock, MapPin, User, Eye, EyeOff, ChevronRight, Sparkles, Copy, X } from 'lucide-react';
import CodeRedemptionModal from './CodeRedemptionModal';
import GlossaryTip from './GlossaryTip';
import { buildDisplayFallback } from '../utils/displayFallback';
import apiService, { aiAnalysisAPI } from '../services/api';
import { useLocation, useNavigate } from 'react-router-dom';
import toast from 'react-hot-toast';

// 四柱干支：干/支分别挂词条（k=原始中文值，children=后端英译展示串）；日柱天干用「日主」词条
const PillarChars = ({ p, day }) => {
    if (!p || !p.stem) return <>Unknown</>;
    return (
        <>
            <GlossaryTip k={day ? `daymaster:${p.stem.key}` : `stem:${p.stem.key}`}>{p.stem.text}</GlossaryTip>
            {' '}
            <GlossaryTip k={`branch:${p.branch.key}`}>{p.branch.text}</GlossaryTip>
        </>
    );
};

// 藏干列表：每字挂天干词条
const HiddenStems = ({ items }) => {
    if (!items || items.length === 0) return <>Unknown</>;
    return (
        <>
            {items.map((s, i) => (
                <span key={i}>{i > 0 ? ', ' : ''}<GlossaryTip k={`stem:${s.key}`}>{s.text}</GlossaryTip></span>
            ))}
        </>
    );
};

// 藏干十神列表：藏干挂天干词条、十神挂十神词条；无详析时退回单值十神
const HiddenGods = ({ items, fallback }) => {
    if (items && items.length > 0) {
        return (
            <>
                {items.map((it, i) => (
                    <span key={i}>
                        {i > 0 ? ', ' : ''}
                        <GlossaryTip k={`stem:${it.stem.key}`}>{it.stem.text}</GlossaryTip>
                        (<GlossaryTip k={`tengod:${it.god.key}`}>{it.god.text}</GlossaryTip>)
                    </span>
                ))}
            </>
        );
    }
    if (fallback && fallback.key) return <GlossaryTip k={`tengod:${fallback.key}`}>{fallback.text}</GlossaryTip>;
    return <>Unknown</>;
};

const ResultsPage = (props) => {
    const location = useLocation();
    const navigate = useNavigate();
    const data = props.data || location.state?.chartData || (() => {
        try { return JSON.parse(localStorage.getItem('li_last_chart') || 'null'); } catch { return null; }
    })();
    const [isVisible, setIsVisible] = useState(false);
    const [hoveredCard, setHoveredCard] = useState(null);
    const [expandedSections, setExpandedSections] = useState({
        bazi: false,
        ziwei: false,
        vedic: false
    });
    const [showPayModal, setShowPayModal] = useState(false);
    const [isGeneratingReport, setIsGeneratingReport] = useState(false);
    const [generationProgress, setGenerationProgress] = useState(0);
    const [currentGenerationStep, setCurrentGenerationStep] = useState('');
    const [showCodeModal, setShowCodeModal] = useState(false);

    useEffect(() => {
        setIsVisible(true);
    }, []);

    // 结果持久化：刷新或误关页面后还能找回这次排盘
    useEffect(() => {
        if (data) {
            try { localStorage.setItem('li_last_chart', JSON.stringify(data)); } catch { /* 存储不可用时忽略 */ }
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);

    // 在线支付直达：支付成功页把已付费的码暂存 li_paid_code，回到结果页自动核销并生成报告，
    // 用户无需再手动输码。核销序列与手动输码完全一致（verify → generate）。
    const autoRedeemTried = React.useRef(false);
    useEffect(() => {
        if (!data || autoRedeemTried.current) return;
        let paidCode = null;
        try { paidCode = localStorage.getItem('li_paid_code'); } catch { /* 存储不可用时忽略 */ }
        if (!paidCode) return;
        autoRedeemTried.current = true;
        try { localStorage.removeItem('li_paid_code'); } catch { /* 忽略 */ }
        (async () => {
            try {
                const r = await fetch(`${API_BASE}/api/redemption-codes/verify`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ code: paidCode })
                });
                if (r.ok) {
                    toast.success('Payment confirmed — building your full report…');
                    generateAIReport(paidCode);
                } else {
                    toast.error('Auto-unlock failed. Tap "Get My Full Report" and enter the recovery code from the payment page.');
                }
            } catch {
                toast.error('Auto-unlock failed. Tap "Get My Full Report" and enter the recovery code from the payment page.');
            }
        })();
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);

    // Free Quick Reading（本地规则引擎，基于本盘真实数据）
    const [quickRead, setQuickRead] = useState({ type: 'comprehensive', loading: true, text: '', summary: '', points: [], suggestions: [], basis: [], error: '' });
    const loadQuickRead = async (type) => {
        if (!data) return;
        setQuickRead(prev => ({ ...prev, type, loading: true, error: '' }));
        try {
            const r = await apiService.localAnalysis(data, type);
            setQuickRead({ type, loading: false, text: typeof r.analysis === 'string' ? r.analysis : '', summary: r.summary || '', points: r.key_points || [], suggestions: r.suggestions || [], basis: r.basis || [], error: '' });
        } catch (e) {
            setQuickRead(prev => ({ ...prev, loading: false, error: 'The quick read could not be generated just now. You can still expand any chart card above to explore your full charts.' }));
        }
    };
    useEffect(() => {
        if (data) loadQuickRead('comprehensive');
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);
    const [shareTip, setShareTip] = useState('');

    // 先判空再解构：直接打开/刷新 /results 时 data 为空，
    // 先解构会抛 TypeError 白屏（守卫原本写在解构之后，永远执行不到）
    if (!data) {
        return (
            <div className="min-h-[50vh] flex flex-col items-center justify-center gap-4 px-4">
                <p className="text-ink-soft">No chart yet — enter your birth details and cast a chart that is yours.</p>
                <button onClick={() => navigate('/')} className="btn-primary px-5 py-2">Cast a Chart</button>
            </div>
        );
    }

    const { input, bazi, ziwei, vedic } = data;
    // 英译展示树（后端 data.display）；旧缓存无此字段时用原始值同构兜底
    const D = data.display || buildDisplayFallback(data);

    // 切换展开状态
    const toggleSection = (section) => {
        setExpandedSections(prev => ({
            ...prev,
            [section]: !prev[section]
        }));
    };

    // Download：把本次排盘整理成文本报告下载（纯本地生成，不经服务器）
    const downloadReport = () => {
        const lines = [];
        lines.push('ChartTrio · Three-Chart Birth Reading');
        lines.push('============================');
        if (input) {
            lines.push(`Birth date: ${input.birth_date || ''}  Birth time: ${input.birth_time || ''}`);
            lines.push(`Birth place: ${input.location_name || ''}  Gender: ${input.gender === 0 ? 'Female' : 'Male'}`);
        }
        if (D.bazi && D.bazi.pillars) {
            lines.push('', '[ BaZi Chart ]');
            lines.push(`Four Pillars: ${D.bazi.pillars.map((p) => `${p.label.replace(' Pillar', '')} ${p.pair}`).join(' · ')}`);
            if (D.bazi.day_master?.text) lines.push(`Day Master: ${D.bazi.day_master.text}${D.bazi.body_strength ? ` (${D.bazi.body_strength})` : ''}`);
            const es = (D.bazi.five_elements || []).map((e) => `${e.text} ${e.count}`).join(' ');
            if (es) lines.push(`Five Elements: ${es}`);
        }
        if (D.ziwei) {
            lines.push('', '[ Zi Wei Dou Shu ]');
            if (D.ziwei.basic?.five_elements_class) lines.push(`Element structure: ${D.ziwei.basic.five_elements_class}`);
            const names = (D.ziwei.star_positions || []).map((sp) => sp.star.text).filter(Boolean);
            if (names.length) lines.push(`Major stars: ${[...new Set(names)].join(', ')}`);
        }
        if (vedic) {
            lines.push('', '[ Vedic Chart ]');
            if (vedic.ascendant?.sign) lines.push(`Ascendant: ${vedic.ascendant.sign}`);
            const pl = vedic.planets || {};
            const ps = Object.entries(pl).map(([k, v]) => `${k}·${v?.sign || ''}${v?.house ? `(House ${v.house})` : ''}`).join('；');
            if (ps) lines.push(`Planets: ${ps}`);
        }
        if (quickRead.text) lines.push('', '[ Free Quick Reading ]', quickRead.text);
        lines.push('', '— Three charts, cross-checked. For reflection only; your fate is in your own hands.');
        const blob = new Blob([lines.join('\n')], { type: 'text/plain;charset=utf-8' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'ChartTrio-Report.txt';
        a.click();
        URL.revokeObjectURL(url);
    };

    // Share：系统分享优先，否则复制文案
    const shareResults = async () => {
        const dm = D.bazi?.day_master?.text ? `Day Master ${D.bazi.day_master.text}` : '';
        const text = `I cast my three-chart birth reading on ChartTrio (BaZi · Zi Wei · Vedic)${dm ? ` — ${dm}` : ''}. Take a look at yours:`;
        const url = window.location.origin + '/';
        try {
            if (navigator.share) {
                await navigator.share({ title: 'ChartTrio · Three Charts, One Reading', text, url });
                return;
            }
            throw new Error('no-native-share');
        } catch (e) {
            try {
                await navigator.clipboard.writeText(`${text} ${url}`);
                setShareTip('Share text copied — paste it to a friend');
            } catch {
                setShareTip('Copy failed — a screenshot works too');
            }
            setTimeout(() => setShareTip(''), 2600);
        }
    };

    // 生成AI报告 - 两阶段调用 + 模拟进度
    const generateAIReport = async (redemptionCode) => {
        setIsGeneratingReport(true);
        setGenerationProgress(0);
        setCurrentGenerationStep('Getting ready...');

        try {
            // 使用兑换码作为订单号
            const orderId = redemptionCode;

            // 只生成prompt文件，不调用AI
            setCurrentGenerationStep('Writing your report...');
            setGenerationProgress(30);

            const response = await fetch(`${API_BASE}/api/ai-report/generate`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    user_data: data,
                    order_id: orderId
                })
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const result = await response.json();
            console.log('Prompt文件生成成功:', result);

            setCurrentGenerationStep('Done — opening your report...');
            setGenerationProgress(100);

            // 跳转到FinalReport页面
            window.location.href = `/final-report/${orderId}`;

        } catch (error) {
            console.error('生成AI报告错误:', error);
            alert(`Could not generate the report: ${error.message}`);
        } finally {
            setIsGeneratingReport(false);
            setGenerationProgress(0);
            setCurrentGenerationStep('');
        }
    };

    const analysisItems = [
        {
            id: "bazi",
            title: "BaZi Chart",
            subtitle: "Chinese Four Pillars astrology",
            gradient: "bg-primary-600",
            bgGradient: "bg-primary-50 border-primary-200 text-primary-700",
            icon: "八",
            progress: 100,
            data: bazi,
        },
        {
            id: "ziwei",
            title: "Zi Wei Dou Shu",
            subtitle: "Chinese star astrology",
            gradient: "bg-secondary-600",
            bgGradient: "bg-secondary-50 border-secondary-200 text-secondary-700",
            icon: "紫",
            progress: 100,
            data: ziwei,
        },
        {
            id: "vedic",
            title: "Vedic Chart",
            subtitle: "Vedic astrology (Jyotish)",
            gradient: "bg-accent-500",
            bgGradient: "bg-accent-50 border-accent-200 text-accent-800",
            icon: "吠",
            progress: 100,
            data: vedic,
        },
    ];

    const userInfo = [
        { label: "Birth date", value: input.birth_date, icon: Calendar, color: "text-primary-600", bg: "bg-primary-50" },
        { label: "Birth time", value: input.birth_time, icon: Clock, color: "text-secondary-600", bg: "bg-secondary-50" },
        { label: "Birth place", value: input.location_name || `${input.longitude}°, ${input.latitude}°`, icon: MapPin, color: "text-accent-700", bg: "bg-accent-50" },
        { label: "Gender", value: D.gender || 'Unknown', icon: User, color: "text-ink-soft", bg: "bg-paper-deep" },
    ];

    return (
        <div className="min-h-screen bg-paper">

            {/* Header */}
            <div className="relative z-10 flex items-center justify-between px-6 py-4 bg-paper-card border-b border-line">
                <button
                    onClick={props.onBack || (() => navigate('/'))}
                    className="flex items-center text-ink-soft hover:text-primary-700 hover:bg-paper-deep transition-colors duration-200 px-3 py-2 rounded"
                >
                    <ArrowLeft className="w-4 h-4 mr-2" />
                    Back
                </button>
            </div>

            {/* Main Content */}
            <div className="relative z-10 max-w-5xl mx-auto px-6 py-8">
                {/* Title Section */}
                <div
                    className={`text-center mb-12 transition-all duration-1000 ${isVisible ? "opacity-100 translate-y-0" : "opacity-0 translate-y-8"}`}
                >
                    <div className="inline-flex items-center gap-2 mb-4">
                        <span className="seal w-8 h-8 text-sm">命</span>
                        <h1 className="text-4xl font-serif font-black text-ink tracking-wide">
                            Your Birth Chart Report
                        </h1>
                        
                    </div>
                    <p className="text-ink-faint text-lg">Three ancient systems, cross-checked — the patterns you were born with, in plain words</p>
                    <div className="mt-2 text-center">
                        <span className="text-ink-soft text-base">
                            Birth date: {input.birth_date || 'Unknown'}
                            <p className="text-xs text-ink-faint mt-1">This result is saved in your current browser, so refreshing is safe. On a different device, cast the chart again.</p>
                            &nbsp;&nbsp;Birth time: {input.birth_time || 'Unknown'}
                            &nbsp;&nbsp;Birth place: {input.location_name || `${input.longitude}°, ${input.latitude}°`}
                            &nbsp;&nbsp;Gender: {D.gender || 'Unknown'}
                        </span>
                    </div>

                    {/* The Full Three-Chart Reading按钮 */}
                    <div className="mt-6 flex justify-center">
                        <button
                            onClick={() => setShowPayModal(true)}
                            className="group relative inline-flex items-center space-x-3 px-6 py-3 bg-primary-600 hover:bg-primary-700 text-paper-card font-semibold rounded shadow-soft transition-colors duration-200"
                        >
                            {/* 钱币图标 */}
                            <div className="seal w-6 h-6">
                                <span className="text-xs font-bold">¥</span>
                            </div>
                            <span className="text-lg">The Full Three-Chart Reading</span>
                            <div className="px-2 py-0.5 bg-paper-card text-primary-700 text-xs font-bold rounded-sm tracking-widest">VIP</div>
                        </button>
                    </div>

                    <div className="mt-6 flex items-center justify-center gap-3"><span className="h-px w-24 bg-accent-400"></span><span className="seal w-5 h-5 text-[10px]">印</span><span className="h-px w-24 bg-accent-400"></span></div>
                </div>

                {/* Analysis Cards */}
                <div className="space-y-6">
                    {analysisItems.map((item, index) => (
                        <div
                            key={item.id}
                            className={`group cursor-pointer transition-all duration-500 border border-line bg-paper-card overflow-hidden rounded hover:border-accent-300 ${isVisible ? "opacity-100 translate-x-0" : "opacity-0 translate-x-8"}`}
                            style={{ transitionDelay: `${600 + index * 200}ms` }}
                            onMouseEnter={() => setHoveredCard(item.id)}
                            onMouseLeave={() => setHoveredCard(null)}
                            onClick={() => toggleSection(item.id)}
                        >
                            <div className="p-0">
                                <div className="flex items-center">
                                    {/* 左侧竖色条 */}
                                    <div className={`w-2 md:w-3 h-24 ${item.gradient} rounded-l mr-6`} />
                                    {/* 图标+内容 */}
                                    <div className="flex items-center space-x-4 flex-1">
                                        <div className="ml-2">
                                            <div className={`w-16 h-16 rounded border ${item.bgGradient} flex items-center justify-center font-serif font-bold text-2xl`}>
                                                {item.icon}
                                            </div>
                                        </div>
                                        <div>
                                            <h3 className="text-xl font-serif font-bold text-ink mb-1">
                                                {item.title}
                                            </h3>
                                            <p className="text-ink-faint mb-3">{item.subtitle}</p>
                                            {/* Progress Bar */}
                                            <div className="w-48 h-1.5 bg-paper-deep rounded-full overflow-hidden">
                                                <div
                                                    className={`h-full ${item.gradient} rounded-full transition-all duration-1000 ease-out`}
                                                    style={{
                                                        width: hoveredCard === item.id ? `${item.progress}%` : "0%",
                                                        transitionDelay: hoveredCard === item.id ? "200ms" : "0ms",
                                                    }}
                                                ></div>
                                            </div>
                                            <p className="text-sm text-ink-faint mt-1">Analysis progress: {item.progress}%</p>
                                        </div>
                                    </div>
                                    {/* 右侧按钮（电脑端） */}
                                    <div className="hidden md:flex items-center space-x-2 mr-4">
                                        <div
                                            className="p-3 rounded-full border border-line bg-paper-deep/60 group-hover:border-accent-300 transition-colors duration-200"
                                        >
                                            {expandedSections[item.id] ?
                                                <EyeOff className="w-5 h-5 text-ink-faint group-hover:text-primary-600 transition-colors duration-200" /> :
                                                <Eye className="w-5 h-5 text-ink-faint group-hover:text-primary-600 transition-colors duration-200" />
                                            }
                                        </div>
                                    </div>
                                    {/* 手机端按钮（下方） */}
                                    <div className="flex md:hidden w-full mt-2 gap-2">
                                        <div
                                            className="p-3 rounded-full border border-line bg-paper-deep/60 group-hover:border-accent-300 transition-colors duration-200"
                                        >
                                            {expandedSections[item.id] ?
                                                <EyeOff className="w-5 h-5 text-ink-faint group-hover:text-primary-600 transition-colors duration-200" /> :
                                                <Eye className="w-5 h-5 text-ink-faint group-hover:text-primary-600 transition-colors duration-200" />
                                            }
                                        </div>
                                    </div>
                                </div>

                                {/* Expanded Content */}
                                {expandedSections[item.id] && item.data && (
                                    <div className="border-t border-line bg-paper-deep/40 p-6">
                                        {item.id === 'bazi' && renderBaziContent(D.bazi, input)}
                                        {item.id === 'ziwei' && renderZiweiContent(D.ziwei)}
                                        {item.id === 'vedic' && renderVedicContent(item.data)}
                                    </div>
                                )}
                            </div>
                        </div>
                    ))}
                </div>
            </div>

            {/* Free Quick Reading：先给价值，再谈付费 */}
            <div className="max-w-6xl mx-auto px-4 mt-8">
                <div className="bg-paper-card border border-line rounded shadow-soft p-5 md:p-7">
                    <div className="flex items-center gap-3 mb-4">
                        <span className="seal w-9 h-9 text-base">读</span>
                        <h3 className="text-xl font-serif font-bold text-ink">Free Quick Reading</h3>
                        <span className="text-xs bg-secondary-50 text-secondary-700 border border-secondary-200 rounded px-2 py-0.5">Generated live from your charts</span>
                    </div>
                    <div className="flex flex-wrap gap-2 mb-4">
                        {[['comprehensive', 'Overview'], ['personality', 'Personality'], ['career', 'Career'], ['wealth', 'Money'], ['relationship', 'Love'], ['health', 'Health']].map(([t, label]) => (
                            <button
                                key={t}
                                onClick={() => loadQuickRead(t)}
                                className={`px-3 py-1.5 rounded text-sm border transition-colors ${quickRead.type === t ? 'bg-primary-600 text-paper-card border-primary-600' : 'bg-paper-card text-ink-soft border-line hover:border-accent-300'}`}
                            >
                                {label}
                            </button>
                        ))}
                    </div>
                    {quickRead.loading ? (
                        <p className="text-ink-faint text-sm py-6 text-center">Reading your charts…</p>
                    ) : quickRead.error ? (
                        <p className="text-primary-700 text-sm py-4">{quickRead.error}</p>
                    ) : (
                        <div className="space-y-3">
                            {quickRead.summary && <p className="text-ink font-medium leading-relaxed text-[15px]">{quickRead.summary}</p>}
                            {quickRead.points.length > 0 && (
                                <ul className="space-y-1.5">
                                    {quickRead.points.map((pt, i) => (
                                        <li key={i} className="text-ink-soft leading-relaxed text-[15px] flex gap-2"><span className="text-primary-600 mt-0.5">·</span><span>{pt}</span></li>
                                    ))}
                                </ul>
                            )}
                            {quickRead.suggestions.length > 0 && (
                                <div className="bg-paper-deep/50 border border-line rounded p-3">
                                    <p className="text-sm font-medium text-ink mb-1">Advice</p>
                                    <ul className="space-y-1">
                                        {quickRead.suggestions.map((sg, i) => (
                                            <li key={i} className="text-sm text-ink-soft leading-relaxed">{sg}</li>
                                        ))}
                                    </ul>
                                </div>
                            )}
                            {quickRead.text.split('\n').filter(Boolean).map((para, i) => (
                                <p key={i} className="text-ink-soft leading-relaxed text-[15px]">{para}</p>
                            ))}
                            {quickRead.basis?.length > 0 && (
                                <p className="text-xs text-ink-faint pt-2 border-t border-line">
                                    Based on: {quickRead.basis.slice(0, 6).join(' · ')}
                                </p>
                            )}
                            <p className="text-xs text-ink-faint">That is the free quick read. The full cross-chart analysis — including your 12-month forecast and the 30-question Q&A — lives in the complete report.</p>
                        </div>
                    )}
                </div>
                <div className="flex gap-3 mt-4">
                    <button onClick={shareResults} className="btn-secondary flex-1 flex items-center justify-center gap-2 py-2.5">
                        <Share2 className="w-4 h-4" /> Share
                    </button>
                    <button onClick={downloadReport} className="btn-secondary flex-1 flex items-center justify-center gap-2 py-2.5">
                        <Download className="w-4 h-4" /> Download
                    </button>
                </div>
            </div>

            {shareTip && (
                <div className="fixed left-1/2 top-20 z-50 -translate-x-1/2 bg-ink text-paper-card px-6 py-2 rounded shadow-soft text-base font-medium">
                    {shareTip}
                </div>
            )}


            {/* 付费弹窗 */}
            {showPayModal && (
                <div className="fixed inset-0 bg-black/60 z-50 flex items-center justify-center p-2 md:p-4">
                    <div className="bg-paper-card frame-double shadow-soft max-w-xs md:max-w-2xl w-full relative overflow-hidden">
                        {/* Decorative background elements */}
                        <div className="p-4 md:p-8 relative z-10">
                            {/* 关闭按钮 */}
                            <button onClick={() => setShowPayModal(false)} className="absolute top-2 right-2 md:top-4 md:right-4 p-2 text-ink-faint hover:text-ink hover:bg-paper-deep rounded-full transition-colors duration-200">
                                <X className="w-5 h-5 md:w-6 md:h-6" />
                            </button>
                            {/* Header */}
                            <div className="text-center mb-4 md:mb-8">
                                <div className="inline-flex items-center gap-2 mb-2 md:mb-4">
                                    <span className="inline-block h-px w-8 bg-accent-400"></span>
                                    <h3 className="text-lg md:text-2xl font-serif font-black text-ink">The Full ChartTrio Report</h3>
                                    <span className="inline-block h-px w-8 bg-accent-400"></span>
                                </div>
                                <p className="text-ink-faint text-sm md:text-base">Unlock the complete reading — all four modules, in plain words</p>
                            </div>
                            {/* Price Display */}
                            <div className="text-center mb-4 md:mb-8">
                                <div className="inline-flex items-baseline gap-2 bg-paper-deep/70 rounded px-4 py-2 md:px-6 md:py-4 border border-line">
                                    <span className="text-ink-faint text-base md:text-lg">Only</span>
                                    <span className="text-2xl md:text-4xl font-serif font-black text-primary-600">$24.90</span>
                                    <span className="text-ink-faint text-xs md:text-sm">USD · one-time</span>
                                </div>
                                <div className="flex justify-center mt-2">
                                    <button
                                        onClick={() => { setShowPayModal(false); navigate('/final-report/LIFEDEMO1995'); }}
                                        className="px-4 py-1 bg-paper-card border border-line text-ink-soft text-xs rounded hover:border-accent-300 hover:text-primary-700 transition-colors duration-200"
                                    >
                                        View a sample
                                    </button>
                                </div>
                            </div>
                            {/* Features Grid */}
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-2 md:gap-4 mb-4 md:mb-8">
                                {[
                                    {
                                        icon: "衡",
                                        title: "Strengths & Blind Spots",
                                        description: "Your three charts read together — where you shine and where you trip",
                                        gradient: "bg-primary-50",
                                    },
                                    {
                                        icon: "图",
                                        title: "Personality Map",
                                        description: "Your chart structure and life themes, mapped out",
                                        gradient: "bg-secondary-50",
                                    },
                                    {
                                        icon: "运",
                                        title: "Your Next 12 Months",
                                        description: "A month-by-month look at the year ahead",
                                        gradient: "bg-accent-50",
                                    },
                                    {
                                        icon: "策",
                                        title: "30 Questions, Answered",
                                        description: "Thirty questions across personality, career, money, love and growth",
                                        gradient: "bg-paper-deep/70",
                                    },
                                ].map((feature, index) => (
                                    <div
                                        key={feature.title}
                                        className={`group p-2 md:p-4 rounded ${feature.gradient} border border-line hover:border-accent-300 transition-colors duration-200`}
                                    >
                                        <div className="flex items-start gap-2 md:gap-3">
                                            <div className="font-serif font-bold text-xl md:text-2xl text-primary-700 flex-shrink-0 w-8 text-center">
                                                {feature.icon}
                                            </div>
                                            <div>
                                                <h4 className="font-semibold text-ink mb-1 text-sm md:text-base">
                                                    {feature.title}
                                                </h4>
                                                <p className="text-xs md:text-sm text-ink-faint">
                                                    {feature.description}
                                                </p>
                                            </div>
                                        </div>
                                    </div>
                                ))}
                            </div>
                            {/* CTA Button */}
                            <div className="text-center">
                                <button
                                    onClick={() => setShowCodeModal(true)}
                                    disabled={isGeneratingReport}
                                    className="bg-primary-600 hover:bg-primary-700 text-paper-card px-6 md:px-12 py-3 md:py-4 text-base md:text-lg font-semibold rounded shadow-soft transition-colors duration-200 relative overflow-hidden group disabled:opacity-50 disabled:cursor-not-allowed"
                                >
                                    <span className="relative z-10">
                                        {isGeneratingReport ? 'Writing your report...' : 'Get My Full Report'}
                                    </span>
                                    {isGeneratingReport && (
                                        <div
                                            className="absolute bottom-0 left-0 h-1 bg-paper-card/40 transition-all duration-300"
                                            style={{ width: `${generationProgress}%` }}
                                        ></div>
                                    )}
                                    </button>
                                <p className="text-ink-faint text-xs mt-2 md:mt-3">
                                    {isGeneratingReport
                                        ? currentGenerationStep || 'Writing your personal report — one moment...'
                                        : 'In-depth reading · Private by design · Works on any device'
                                    }
                                </p>
                            </div>
                        </div>
                    </div>
                </div>
            )}

            {/* 付费悬浮窗 */}
            <CodeRedemptionModal
                isOpen={showCodeModal}
                onClose={() => setShowCodeModal(false)}
            />

            {/* Inline Styles for animations */}
            <style jsx>{`
                @keyframes float {
                    0%, 100% { transform: translateY(0px); }
                    50% { transform: translateY(-10px); }
                }
                .animate-float {
                    animation: float 3s ease-in-out infinite;
                }
                @keyframes fade-in-out {
                    0% { opacity: 0; transform: translateY(-10px); }
                    10% { opacity: 1; transform: translateY(0); }
                    90% { opacity: 1; transform: translateY(0); }
                    100% { opacity: 0; transform: translateY(-10px); }
                }
                .animate-fade-in-out {
                    animation: fade-in-out 1.5s;
                }
            `}</style>
        </div>
    );

    // 渲染八字内容
    function renderBaziContent(db, input) {
        return (
            <div className="space-y-6">
                <p className="text-xs text-ink-faint">Tip: words with a <span className="border-b border-dotted border-primary-500/60 text-ink-soft">dotted underline</span> have a plain-words explanation — hover (or tap on mobile) to read it.</p>
                {/* 真太阳时信息 */}
                {input.true_solar_time && (
                    <div className="bg-accent-50 border border-accent-200 rounded p-4">
                        <h4 className="font-serif font-bold text-accent-800 mb-2">True Solar Time Correction</h4>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                            <div>
                                <span className="text-accent-700">Clock time: </span>
                                <span className="font-medium text-ink ml-2">
                                    {input.birth_date} {input.birth_time}
                                </span>
                            </div>
                            <div>
                                <span className="text-accent-700">True solar time: </span>
                                <span className="font-medium text-ink ml-2">
                                    {input.true_solar_time.year}-
                                    {String(input.true_solar_time.month).padStart(2, '0')}-
                                    {String(input.true_solar_time.day).padStart(2, '0')} {' '}
                                    {String(input.true_solar_time.hour).padStart(2, '0')}:
                                    {String(input.true_solar_time.minute).padStart(2, '0')}
                                </span>
                            </div>
                        </div>
                    </div>
                )}

                {/* 四柱表格 */}
                <div>
                    <h4 className="font-serif font-bold text-ink mb-4">The Four Pillars</h4>
                    <div className="overflow-x-auto">
                        <table className="w-full border-collapse">
                            <thead>
                                <tr className="bg-paper-deep/70">
                                    <th className="border border-line px-4 py-3 text-left font-medium text-ink-soft">Pillar</th>
                                    <th className="border border-line px-4 py-3 text-left font-medium text-ink-soft">Stem & Branch</th>
                                    <th className="border border-line px-4 py-3 text-left font-medium text-ink-soft">NaYin</th>
                                    <th className="border border-line px-4 py-3 text-left font-medium text-ink-soft">Hidden Stems</th>
                                    <th className="border border-line px-4 py-3 text-left font-medium text-ink-soft">Ten God</th>
                                </tr>
                            </thead>
                            <tbody>
                                {db.pillars.map((p) => (
                                    <tr key={p.key} className={p.key === 'day' ? 'bg-accent-50' : ''}>
                                        <td className="border border-line px-4 py-3 font-medium text-ink-soft">{p.label}{p.key === 'day' ? ' (Day Master)' : ''}</td>
                                        <td className={`border border-line px-4 py-3 ${p.key === 'day' ? 'text-primary-700 font-serif font-black text-lg' : 'text-primary-600 font-serif font-bold'}`}><PillarChars p={p} day={p.key === 'day'} /></td>
                                        <td className="border border-line px-4 py-3 text-secondary-600">{p.nayin || 'Unknown'}</td>
                                        <td className="border border-line px-4 py-3 text-ink-soft">
                                            <HiddenStems items={p.hidden_stems} />
                                        </td>
                                        <td className="border border-line px-4 py-3 text-accent-700">
                                            <HiddenGods items={p.hidden_gods} fallback={p.ten_god} />
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>

                {/* Five Elements */}
                {db.five_elements && db.five_elements.length > 0 && (
                    <div>
                        <h4 className="font-serif font-bold text-ink mb-4">Five Elements</h4>
                        <div className="space-y-3">
                            {db.five_elements.map((e) => (
                                <div key={e.key} className="flex items-center justify-between">
                                    <span className="text-ink-soft"><GlossaryTip k={`element:${e.key}`}>{e.text}</GlossaryTip></span>
                                    <div className="flex items-center space-x-3 flex-1 max-w-xs">
                                        <div className="flex-1 bg-paper-deep rounded-full h-2">
                                            <div
                                                className="bg-primary-500 h-2 rounded-full transition-all duration-1000"
                                                style={{ width: `${(e.count / Math.max(...db.five_elements.map((x) => x.count))) * 100}%` }}
                                            ></div>
                                        </div>
                                        <span className="text-ink-soft text-sm w-8">{e.count}</span>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                )}

                {/* 综合分析 */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div>
                        <h4 className="font-serif font-bold text-ink mb-4">Chart Basics</h4>
                        <div className="space-y-3">
                            <div className="p-4 bg-primary-50 border border-primary-100 rounded">
                                <p className="text-sm text-primary-600 mb-1">Day Master</p>
                                <p className="font-bold text-ink font-serif text-lg">{db.day_master?.key ? <GlossaryTip k={`daymaster:${db.day_master.key}`}>{db.day_master.text}</GlossaryTip> : 'Unknown'}</p>
                            </div>
                            <div className="p-4 bg-secondary-50 border border-secondary-100 rounded">
                                <p className="text-sm text-secondary-600 mb-1">Day Master Strength</p>
                                <p className="font-bold text-ink font-serif text-lg">{db.body_strength || 'Unknown'}</p>
                            </div>

                        </div>
                    </div>

                    <div>
                        <h4 className="font-serif font-bold text-ink mb-4">Ten Gods Pattern</h4>
                        <div className="space-y-2">
                            {db.ten_gods && db.ten_gods.map((row) => (
                                <div key={row.position} className="flex justify-between p-3 bg-paper-card border border-line rounded">
                                    <span className="text-ink-faint">{row.position}:</span>
                                    <span className="font-medium text-ink"><GlossaryTip k={`tengod:${row.god.key}`}>{row.god.text}</GlossaryTip></span>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>


            </div>
        );
    }

    // 渲染紫微斗数内容
    function renderZiweiContent(dz) {
        return (
            <div className="space-y-6">
                <p className="text-xs text-ink-faint">Tip: words with a <span className="border-b border-dotted border-primary-500/60 text-ink-soft">dotted underline</span> have a plain-words explanation — hover (or tap on mobile) to read it.</p>
                {/* Basics */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div>
                        <h4 className="font-serif font-bold text-ink mb-4">Basics</h4>
                        <div className="space-y-3">
                            <div className="flex justify-between p-3 bg-paper-card border border-line rounded">
                                <span className="text-ink-faint">Life Palace star: </span>
                                <span className="font-medium text-ink">{dz.basic?.soul?.key ? <GlossaryTip k={`star:${dz.basic.soul.key}`}>{dz.basic.soul.text}</GlossaryTip> : 'Unknown'}</span>
                            </div>
                            <div className="flex justify-between p-3 bg-paper-card border border-line rounded">
                                <span className="text-ink-faint">Body Palace star: </span>
                                <span className="font-medium text-ink">{dz.basic?.body?.key ? <GlossaryTip k={`star:${dz.basic.body.key}`}>{dz.basic.body.text}</GlossaryTip> : 'Unknown'}</span>
                            </div>
                            <div className="flex justify-between p-3 bg-paper-card border border-line rounded">
                                <span className="text-ink-faint">Element bureau: </span>
                                <span className="font-medium text-ink">{dz.basic?.five_elements_class || 'Unknown'}</span>
                            </div>
                            <div className="flex justify-between p-3 bg-paper-card border border-line rounded">
                                <span className="text-ink-faint">Lunar date: </span>
                                <span className="font-medium text-ink">{dz.basic?.lunar_date || 'Unknown'}</span>
                            </div>
                            <div className="flex justify-between p-3 bg-paper-card border border-line rounded">
                                <span className="text-ink-faint">Year stem-branch: </span>
                                <span className="font-medium text-ink">{dz.basic?.chinese_date || 'Unknown'}</span>
                            </div>
                        </div>
                    </div>

                    <div>
                        <h4 className="font-serif font-bold text-ink mb-4">Year Transformations</h4>
                        <div className="space-y-3">
                            {dz.year_four_trans && dz.year_four_trans.map((t) => (
                                <div key={t.type.key} className="flex justify-between p-3 bg-secondary-50 border border-secondary-100 rounded">
                                    <span className="text-secondary-700 font-medium"><GlossaryTip k={`sihua:${t.type.key}`}>{t.type.text}</GlossaryTip>:</span>
                                    <span className="font-medium text-ink"><GlossaryTip k={`star:${t.star.key}`}>{t.star.text}</GlossaryTip></span>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>

                {/* 十四主星位置 */}
                <div>
                    <h4 className="font-serif font-bold text-ink mb-4">The 14 Major Stars</h4>
                    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
                        {dz.star_positions && dz.star_positions.map((sp) => (
                            <div key={sp.star.key} className="flex justify-between p-3 bg-secondary-50 border border-secondary-100 rounded">
                                <span className="text-secondary-700 font-medium"><GlossaryTip k={`star:${sp.star.key}`}>{sp.star.text}</GlossaryTip></span>
                                <span className="text-ink"><GlossaryTip k={`palace:${sp.palace.key}`}>{sp.palace.text}</GlossaryTip></span>
                            </div>
                        ))}
                    </div>
                </div>

                {/* 十二宫详细信息 */}
                <div>
                    <h4 className="font-serif font-bold text-ink mb-4">The Twelve Palaces</h4>
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                        {dz.palaces && dz.palaces.map((palace) => (
                            <div key={palace.name.key} className="bg-paper-card border border-line rounded p-4">
                                <div className="flex items-center justify-between mb-3">
                                    <h5 className="font-semibold text-ink font-serif"><GlossaryTip k={`palace:${palace.name.key}`}>{palace.name.text}</GlossaryTip></h5>
                                    {palace.is_body_palace && (
                                        <span className="px-2 py-0.5 bg-primary-600 text-paper-card text-xs rounded-sm tracking-widest">Body</span>
                                    )}
                                </div>
                                <div className="space-y-2 text-sm">
                                    <div>
                                        <span className="text-ink-faint">Palace: </span>
                                        <span className="font-medium text-ink"><GlossaryTip k={`stem:${palace.stem.key}`}>{palace.stem.text}</GlossaryTip>{' '}<GlossaryTip k={`branch:${palace.branch.key}`}>{palace.branch.text}</GlossaryTip></span>
                                    </div>
                                    {palace.major_stars && palace.major_stars.length > 0 && (
                                        <div>
                                            <span className="text-ink-faint">Major stars: </span>
                                            <div className="mt-1">
                                                {palace.major_stars.map((star, idx) => (
                                                    <span key={idx} className="inline-block mr-2 mb-1 px-2 py-1 bg-secondary-50 border border-secondary-100 text-secondary-700 text-xs rounded-sm">
                                                        <GlossaryTip k={`star:${star.name.key}`}>{star.name.text}</GlossaryTip>
                                                        {star.brightness && ` (${star.brightness})`}
                                                        {star.mutagen && <> [<GlossaryTip k={`sihua:${star.mutagen.key}`}>{star.mutagen.text}</GlossaryTip>]</>}
                                                    </span>
                                                ))}
                                            </div>
                                        </div>
                                    )}
                                    {palace.minor_stars && palace.minor_stars.length > 0 && (
                                        <div>
                                            <span className="text-ink-faint">Support stars: </span>
                                            <div className="mt-1">
                                                {palace.minor_stars.map((star, idx) => (
                                                    <span key={idx} className="inline-block mr-1 mb-1 px-2 py-1 bg-paper-deep border border-line text-ink-soft text-xs rounded-sm">
                                                        <GlossaryTip k={`star:${star.key}`}>{star.text}</GlossaryTip>
                                                    </span>
                                                ))}
                                            </div>
                                        </div>
                                    )}
                                    {palace.adjective_stars && palace.adjective_stars.length > 0 && (
                                        <div>
                                            <span className="text-ink-faint">Challenging stars: </span>
                                            <div className="mt-1">
                                                {palace.adjective_stars.map((star, idx) => (
                                                    <span key={idx} className="inline-block mr-1 mb-1 px-2 py-1 bg-primary-50 border border-primary-100 text-primary-700 text-xs rounded-sm">
                                                        {star.text}
                                                    </span>
                                                ))}
                                            </div>
                                        </div>
                                    )}
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            </div>
        );
    }

    // 渲染印度星盘内容  
    function renderVedicContent(vedic) {
        return (
            <div className="space-y-6">
                <p className="text-xs text-ink-faint">Tip: words with a <span className="border-b border-dotted border-primary-500/60 text-ink-soft">dotted underline</span> have a plain-words explanation — hover (or tap on mobile) to read it.</p>
                {/* Basics */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div>
                        <h4 className="font-serif font-bold text-ink mb-4">Basics</h4>
                        <div className="space-y-3">
                            <div className="flex justify-between p-3 bg-paper-card border border-line rounded">
                                <span className="text-ink-faint">Chart type: </span>
                                <span className="font-medium text-ink">{vedic.chart_type || 'Unknown'}</span>
                            </div>
                            <div className="flex justify-between p-3 bg-paper-card border border-line rounded">
                                <span className="text-ink-faint">Ayanamsa: </span>
                                <span className="font-medium text-ink">{vedic.ayanamsa?.type} ({vedic.ayanamsa?.value}°)</span>
                            </div>
                            <div className="flex justify-between p-3 bg-paper-card border border-line rounded">
                                <span className="text-ink-faint">Ascendant: </span>
                                <span className="font-medium text-ink">{vedic.ascendant?.sign ? <GlossaryTip k={`sign:${vedic.ascendant.sign}`}>{vedic.ascendant.sign}</GlossaryTip> : 'Unknown'} (House {vedic.ascendant?.house} · {vedic.ascendant?.lon?.toFixed(2)}°)</span>
                            </div>
                            <div className="flex justify-between p-3 bg-paper-card border border-line rounded">
                                <span className="text-ink-faint">Calculated at: </span>
                                <span className="font-medium text-ink">{vedic.input?.date} {vedic.input?.time} {vedic.input?.timezone}</span>
                            </div>
                            <div className="flex justify-between p-3 bg-paper-card border border-line rounded">
                                <span className="text-ink-faint">Coordinates: </span>
                                <span className="font-medium text-ink">{vedic.input?.latitude}°N, {vedic.input?.longitude}°E</span>
                            </div>
                        </div>
                    </div>

                    <div>
                        <h4 className="font-serif font-bold text-ink mb-4">Key Angles</h4>
                        <div className="space-y-3">
                            {vedic.axis_points && Object.entries(vedic.axis_points).map(([point, data]) => (
                                <div key={point} className="flex justify-between p-3 bg-accent-50 border border-accent-200 rounded">
                                    <span className="text-accent-700 font-medium">{point}:</span>
                                    <span className="font-medium text-ink">
                                        <GlossaryTip k={`sign:${data.sign}`}>{data.sign}</GlossaryTip> (House {data.house} · {data.lon?.toFixed(2)}°)
                                    </span>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>

                {/* 九大行星位置 */}
                <div>
                    <h4 className="font-serif font-bold text-ink mb-4">The Nine Planets</h4>
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                        {vedic.planets && Object.entries(vedic.planets).map(([planet, data]) => {
                            // 转换行星名称
                            const planetName = planet === 'North Node' ? 'Rahu' :
                                planet === 'South Node' ? 'Ketu' : planet;

                            return (
                                <div key={planet} className="bg-accent-50/60 border border-accent-200 rounded p-4">
                                    <div className="flex items-center justify-between mb-2">
                                        <h5 className="font-semibold text-ink font-serif"><GlossaryTip k={`planet:${planetName}`}>{planetName}</GlossaryTip></h5>
                                        <span className="text-sm text-accent-700">House {data.house}</span>
                                    </div>
                                    <div className="space-y-1 text-sm">
                                        <div className="flex justify-between">
                                            <span className="text-ink-faint">Sign: </span>
                                            <span className="font-medium text-ink"><GlossaryTip k={`sign:${data.sign}`}>{data.sign}</GlossaryTip></span>
                                        </div>
                                        <div className="flex justify-between">
                                            <span className="text-ink-faint">Degree: </span>
                                            <span className="font-medium text-ink">{data.lon?.toFixed(2)}°</span>
                                        </div>
                                    </div>
                                </div>
                            );
                        })}
                    </div>
                </div>

                {/* Planets by House */}
                <div>
                    <h4 className="font-serif font-bold text-ink mb-4">Planets by House</h4>
                    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
                        {(() => {
                            // 统计每个宫位的行星
                            const houseStats = {};
                            if (vedic.planets) {
                                Object.entries(vedic.planets).forEach(([planet, data]) => {
                                    const house = data.house;
                                    if (!houseStats[house]) houseStats[house] = [];
                                    // 转换行星名称
                                    const planetName = planet === 'North Node' ? 'Rahu' :
                                        planet === 'South Node' ? 'Ketu' : planet;
                                    houseStats[house].push(planetName);
                                });
                            }

                            return Array.from({ length: 12 }, (_, i) => i + 1).map(houseNum => (
                                <div key={houseNum} className="bg-paper-card border border-line rounded p-3">
                                    <div className="font-semibold text-ink font-serif mb-2">House {houseNum}</div>
                                    <div className="space-y-1">
                                        {houseStats[houseNum] ? houseStats[houseNum].map((planetName, idx) => (
                                            <span key={idx} className="inline-block mr-1 mb-1 px-2 py-1 bg-accent-50 border border-accent-200 text-accent-800 text-xs rounded-sm">
                                                <GlossaryTip k={`planet:${planetName}`}>{planetName}</GlossaryTip>
                                            </span>
                                        )) : (
                                            <span className="text-ink-faint text-xs">Empty</span>
                                        )}
                                    </div>
                                </div>
                            ));
                        })()}
                    </div>
                </div>

                {/* Planets by Sign */}
                <div>
                    <h4 className="font-serif font-bold text-ink mb-4">Planets by Sign</h4>
                    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
                        {(() => {
                            // 统计每个星座的行星
                            const signStats = {};
                            if (vedic.planets) {
                                Object.entries(vedic.planets).forEach(([planet, data]) => {
                                    const sign = data.sign;
                                    if (!signStats[sign]) signStats[sign] = [];
                                    // 转换行星名称
                                    const planetName = planet === 'North Node' ? 'Rahu' :
                                        planet === 'South Node' ? 'Ketu' : planet;
                                    signStats[sign].push(planetName);
                                });
                            }

                            return Object.entries(signStats).map(([sign, planets]) => (
                                <div key={sign} className="bg-paper-card border border-line rounded p-3">
                                    <div className="font-semibold text-ink font-serif mb-2"><GlossaryTip k={`sign:${sign}`}>{sign}</GlossaryTip></div>
                                    <div className="space-y-1">
                                        {planets.map((planetName, idx) => (
                                            <span key={idx} className="inline-block mr-1 mb-1 px-2 py-1 bg-paper-deep border border-line text-ink-soft text-xs rounded-sm">
                                                <GlossaryTip k={`planet:${planetName}`}>{planetName}</GlossaryTip>
                                            </span>
                                        ))}
                                    </div>
                                </div>
                            ));
                        })()}
                    </div>
                </div>
            </div>
        );
    }
};

export default ResultsPage; 