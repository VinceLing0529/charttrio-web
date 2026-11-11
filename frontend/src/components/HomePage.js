import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import BirthInfoForm from './BirthInfoForm';
import LoadingSpinner from './LoadingSpinner';

const HomePage = () => {
    const [chartData, setChartData] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const navigate = useNavigate();

    const handleChartCalculated = (data) => {
        setChartData(data);
        setError(null);
        // 导航到结果页面，传递数据
        navigate('/results', { state: { chartData: data } });
    };

    const handleError = (error) => {
        setError(error);
        setChartData(null);
    };

    const handleReset = () => {
        setChartData(null);
        setError(null);
    };

    return (
        <main className="container mx-auto px-6 py-4 flex-1">
            {loading && (
                <div className="flex justify-center items-center h-64">
                    <LoadingSpinner />
                </div>
            )}

            {error && (
                <div className="max-w-2xl mx-auto mb-8">
                    <div className="bg-primary-50 border border-primary-200 rounded p-4">
                        <div className="flex items-center">
                            <div className="flex-shrink-0">
                                <svg className="h-5 w-5 text-primary-600" viewBox="0 0 20 20" fill="currentColor">
                                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                                </svg>
                            </div>
                            <div className="ml-3">
                                <h3 className="text-sm font-medium text-primary-800">Something Went Wrong</h3>
                                <div className="mt-2 text-sm text-primary-700">
                                    <p>{error}</p>
                                </div>
                                <div className="mt-4">
                                    <button
                                        onClick={handleReset}
                                        className="bg-primary-600 hover:bg-primary-700 text-paper-card font-medium py-2 px-4 rounded transition-colors duration-200"
                                    >
                                        Start Over
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            )}

            {!chartData && !loading && (
                <div className="w-full max-w-4xl mx-auto flex flex-col justify-start pt-4 md:pt-8">
                    {/* 主标题 */}
                    <div className="text-center mb-6">
                        <div className="flex justify-center mb-3">
                            <span className="seal w-11 h-11 text-xl">命</span>
                        </div>
                        <h1 className="text-3xl lg:text-4xl font-serif font-black text-ink tracking-[0.2em] mb-3">
                            ChartTrio
                        </h1>
                        <div className="flex items-center justify-center gap-3 mb-3">
                            <span className="h-px w-16 bg-accent-400" />
                            <span className="text-[11px] tracking-[0.5em] text-ink-faint">BAZI · ZI WEI · VEDIC</span>
                            <span className="h-px w-16 bg-accent-400" />
                        </div>
                        <div className="space-y-1.5 mb-4">
                            <p className="text-base lg:text-lg text-ink font-serif">Should you take that leap this year?</p>
                            <p className="text-base lg:text-lg text-ink font-serif">Why does money keep slipping through your fingers?</p>
                            <p className="text-base lg:text-lg text-ink font-serif">Is this relationship still worth it?</p>
                        </div>
                        <p className="text-ink-soft text-sm lg:text-base max-w-xl mx-auto leading-relaxed">Your chart will not make decisions for you. It lays out your strengths, your blind spots, and the rhythm of your next few years — cross-checked across three systems: BaZi, Zi Wei, and Vedic astrology — in plain words.</p>
                        <p className="text-ink-faint text-xs lg:text-sm mt-3">Free birth chart & quick reading · Full report $24.90 (your next 12 months, plus 30 life questions answered)</p>
                        <p className="text-ink-faint text-xs mt-2 tracking-wide">Enter your birth details → See your three charts → Read your reading · No sign-up</p>
                    </div>

                    <>
                        <BirthInfoForm
                            onCalculated={handleChartCalculated}
                            onError={handleError}
                            onLoadingChange={setLoading}
                        />
                        <div className="mt-6 bg-secondary-50 border border-secondary-200 rounded p-4 text-left">
                            <p className="text-[11px] tracking-[0.3em] text-secondary-700 mb-2">IN PLAIN WORDS · FROM A SAMPLE REPORT</p>
                            <p className="text-sm text-ink leading-relaxed">"Money in the bank first, romance second. Sleep enough before you hustle."</p>
                            <p className="text-sm text-ink-soft leading-relaxed mt-1.5">"Working hard while you are young is normal for you — your stride comes later, and life gets smoother after your mid-thirties."</p>
                            <p className="mt-3">
                                <button onClick={() => navigate('/final-report/LIFEDEMO1995')} className="text-sm text-primary-700 underline underline-offset-4 decoration-accent-300 hover:text-primary-800">
                                    See a full sample report first →
                                </button>
                            </p>
                        </div>
                    </>
                </div>
            )}
        </main>
    );
};

export default HomePage; 