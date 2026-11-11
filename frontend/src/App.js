import React, { useState, useEffect } from 'react';
import { API_BASE } from './config';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import { Eye, X } from 'lucide-react';
import HomePage from './components/HomePage';
import Header from './components/Header';
import Footer from './components/Footer';
import BirthInfoForm from './components/BirthInfoForm';
import ResultsPage from './components/ResultsPage';
import FinalReport from './components/FinalReport';
import PaymentSuccessPage from './components/PaymentSuccessPage';
import InteractiveMindMapPage from './components/InteractiveMindMapPage';
import FortuneChartPage from './components/FortuneChartPage';
import QAPage from './components/QAPage';
import AnalysisPage from './components/AnalysisPage';
import PromptAdminPage from './components/PromptAdminPage';
import RedemptionCodeAdmin from './components/RedemptionCodeAdmin';
import ManageAdminPage from './components/ManageAdminPage';
import './index.css';

function App() {
    const [data, setData] = useState(null);
    const [showResults, setShowResults] = useState(false);
    const [showAnalysisModal, setShowAnalysisModal] = useState(false);
    const [analysisOrderInput, setAnalysisOrderInput] = useState('');

    const handleDataSubmit = (formData) => {
        setData(formData);
        setShowResults(true);
    };

    const handleBack = () => {
        setShowResults(false);
        setData(null);
    };

    const handleError = (error) => {
        console.error('表单错误:', error);
    };

    const handleLoadingChange = (loading) => {
        // 可以在这里处理加载状态
    };

    const handleShowAnalysisModal = () => {
        setShowAnalysisModal(true);
    };

    const handleLoadHistoryReport = async () => {
        // 清洗：去掉空格/全角空格等空白字符，避免复制粘贴带入不可见字符导致查不到
        const orderId = analysisOrderInput.replace(/\s+/g, '');
        if (!orderId) {
            alert('Please enter your order ID');
            return;
        }

        try {
            const response = await fetch(`${API_BASE}/api/ai-report/report/${encodeURIComponent(orderId)}`);
            if (response.ok) {
                const data = await response.json();
                window.location.href = `/final-report/${encodeURIComponent(orderId)}`;
                setShowAnalysisModal(false);
                setAnalysisOrderInput('');
            } else {
                alert('No report found for that order ID — please double-check it and try again');
            }
        } catch (error) {
            console.error('加载历史报告失败:', error);
            alert('Loading failed — please check your connection');
        }
    };

    // 注入神秘学动画样式
    useEffect(() => {
        const styles = `
          @keyframes float {
            0%, 100% { transform: translateY(0px) translateX(0px) rotate(0deg); }
            25% { transform: translateY(-20px) translateX(10px) rotate(45deg); }
            50% { transform: translateY(-10px) translateX(-8px) rotate(90deg); }
            75% { transform: translateY(-25px) translateX(12px) rotate(135deg); }
          }
          
          @keyframes gentleGlow {
            0% { 
              opacity: 0.3; 
              filter: blur(1px);
            }
            100% { 
              opacity: 0.7; 
              filter: blur(0px);
            }
          }
          
          @keyframes rotate {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
          }
          
          @keyframes shimmer {
            0% { transform: translateX(-100%); }
            100% { transform: translateX(100%); }
          }
          
          .mystical-card {
            position: relative;
            overflow: hidden;
          }
          
          .mystical-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: -100%;
            width: 100%;
            height: 100%;
            background: linear-gradient(90deg, transparent, rgba(148, 163, 184, 0.05), transparent);
            animation: shimmer 12s ease-in-out infinite;
          }
        `;

        const styleSheet = document.createElement("style");
        styleSheet.innerText = styles;
        document.head.appendChild(styleSheet);
        return () => {
            if (document.head.contains(styleSheet)) {
                document.head.removeChild(styleSheet);
            }
        };
    }, []);

    return (
        <Router>
            <div className="min-h-screen bg-paper relative flex flex-col overflow-x-hidden scroll-smooth">
                <Toaster
                    position="top-right"
                    toastOptions={{
                        duration: 4000,
                        style: {
                            background: '#fffdf7',
                            color: '#211d19',
                            boxShadow: '0 2px 8px rgba(33, 29, 25, 0.10)',
                            border: '1px solid #e2d8c4',
                            borderRadius: '4px',
                        },
                    }}
                />

                {/* 顶部朱砂线 */}
                <div className="h-[3px] bg-primary-700 flex-shrink-0" />

                <div className="relative z-10 flex flex-col min-h-screen">
                    <Header onShowAnalysisModal={handleShowAnalysisModal} />

                    <Routes>
                        <Route path="/" element={<HomePage />} />
                        <Route path="/results" element={<ResultsPage />} />
                        <Route path="/final-report/:orderId" element={<FinalReport />} />
                        <Route path="/payment/success" element={<PaymentSuccessPage />} />
                        <Route path="/final-report/:orderId/interactive-mind-map" element={<InteractiveMindMapPage />} />
                        <Route path="/final-report/:orderId/fortune-chart" element={<FortuneChartPage />} />
                        <Route path="/final-report/:orderId/qa" element={<QAPage />} />
                        <Route path="/final-report/:orderId/analysis" element={<AnalysisPage />} />
                        <Route path="/manage" element={<ManageAdminPage />} />
                    </Routes>

                    <Footer />
                </div>

                {/* 全局View My Report弹窗 */}
                {showAnalysisModal && (
                    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-[9999] flex items-center justify-center p-4">
                        <div className="bg-paper-card border border-line rounded shadow-2xl max-w-md w-full">
                            <div className="flex items-center justify-between p-6 border-b border-line">
                                <h3 className="text-xl font-bold text-ink font-serif">View My Report</h3>
                                <button
                                    onClick={() => {
                                        setShowAnalysisModal(false);
                                        setAnalysisOrderInput('');
                                    }}
                                    className="p-2 hover:bg-paper-deep text-ink-faint hover:text-ink rounded transition-colors duration-300"
                                >
                                    <X className="w-5 h-5" />
                                </button>
                            </div>
                            <div className="p-6">
                                <div className="mb-4">
                                    <label className="block text-sm font-medium text-ink-soft mb-2">
                                        Enter your order ID
                                    </label>
                                    <input
                                        type="text"
                                        maxLength={64}
                                        value={analysisOrderInput}
                                        onChange={(e) => setAnalysisOrderInput(e.target.value)}
                                        placeholder="e.g. LIFE1234ABCD"
                                        className="w-full px-4 py-3 bg-paper-card border border-line rounded text-ink placeholder:text-ink-faint focus:outline-none focus:ring-1 focus:ring-primary-500 focus:border-primary-500"
                                        onKeyPress={(e) => {
                                            if (e.key === 'Enter') {
                                                handleLoadHistoryReport();
                                            }
                                        }}
                                    />
                                </div>
                                <div className="flex gap-3">
                                    <button
                                        onClick={handleLoadHistoryReport}
                                        className="flex-1 bg-primary-600 hover:bg-primary-700 text-paper-card font-medium py-3 px-4 rounded transition-colors duration-200"
                                    >
                                        Open Report
                                    </button>
                                    <button
                                        onClick={() => {
                                            setShowAnalysisModal(false);
                                            setAnalysisOrderInput('');
                                        }}
                                        className="px-4 py-3 bg-paper-deep hover:bg-line text-ink-soft rounded transition-colors duration-200"
                                    >
                                        Cancel
                                    </button>
                                </div>
                                <div className="mt-4 text-center">
                                </div>
                            </div>
                        </div>
                    </div>
                )}
            </div>
        </Router>
    );
}

export default App; 