import React, { useState } from 'react';
import { Brain, Zap, MessageSquare, User, Briefcase, Heart, Activity } from 'lucide-react';
import LoadingSpinner from './LoadingSpinner';

const AnalysisPanel = ({
    chartData,
    analysisData,
    onAnalyze,
    onLocalAnalyze,
    loading
}) => {
    const [selectedType, setSelectedType] = useState('comprehensive');
    const [customQuestion, setCustomQuestion] = useState('');

    const analysisTypes = [
        {
            id: 'personality',
            label: '性格分析',
            icon: User,
            description: '分析性格特点、天赋才能、心理倾向',
            color: 'text-primary-600'
        },
        {
            id: 'career',
            label: '事业发展',
            icon: Briefcase,
            description: '分析适合行业、职业选择、工作运势',
            color: 'text-secondary-600'
        },
        {
            id: 'relationship',
            label: '感情婚姻',
            icon: Heart,
            description: '分析感情观念、婚姻运势、人际关系',
            color: 'text-accent-600'
        },
        {
            id: 'health',
            label: '健康状况',
            icon: Activity,
            description: '分析体质特点、健康建议、养生要点',
            color: 'text-green-600'
        },
        {
            id: 'comprehensive',
            label: '综合分析',
            icon: Brain,
            description: '全面分析各个生活层面',
            color: 'text-purple-600'
        }
    ];

    const handleAnalyze = (type) => {
        if (type === 'chatgpt') {
            onAnalyze(selectedType, customQuestion);
        } else {
            onLocalAnalyze(selectedType);
        }
    };

    if (loading) {
        return (
            <div className="min-h-[400px] flex items-center justify-center">
                <LoadingSpinner text="正在分析中，请稍候..." />
            </div>
        );
    }

    return (
        <div className="space-y-6">
            {!analysisData ? (
                <>
                    {/* 分析类型选择 */}
                    <div>
                        <h3 className="text-lg font-semibold text-gray-800 mb-4">选择分析类型</h3>
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                            {analysisTypes.map((type) => {
                                const Icon = type.icon;
                                return (
                                    <button
                                        key={type.id}
                                        onClick={() => setSelectedType(type.id)}
                                        className={`p-4 rounded-lg border-2 transition-all duration-200 text-left ${selectedType === type.id
                                            ? 'border-primary-500 bg-primary-50'
                                            : 'border-gray-200 hover:border-gray-300'
                                            }`}
                                    >
                                        <div className="flex items-start space-x-3">
                                            <Icon className={`w-6 h-6 mt-1 ${type.color}`} />
                                            <div>
                                                <h4 className="font-medium text-gray-800">{type.label}</h4>
                                                <p className="text-sm text-gray-600 mt-1">{type.description}</p>
                                            </div>
                                        </div>
                                    </button>
                                );
                            })}
                        </div>
                    </div>

                    {/* 自定义问题 */}
                    <div>
                        <label className="form-label">自定义问题（可选）</label>
                        <textarea
                            value={customQuestion}
                            onChange={(e) => setCustomQuestion(e.target.value)}
                            placeholder="输入您想了解的具体问题，如：我适合从事什么行业？何时结婚比较好？"
                            className="form-input h-20 resize-none"
                        />
                    </div>

                    {/* 分析按钮 */}
                    <div className="flex flex-col sm:flex-row gap-4">
                        <button
                            onClick={() => handleAnalyze('chatgpt')}
                            disabled={loading}
                            className="btn-primary flex-1 flex items-center justify-center"
                        >
                            <MessageSquare className="w-4 h-4 mr-2" />
                            ChatGPT 智能分析
                        </button>

                        <button
                            onClick={() => handleAnalyze('local')}
                            disabled={loading}
                            className="btn-secondary flex-1 flex items-center justify-center"
                        >
                            <Zap className="w-4 h-4 mr-2" />
                            本地规则分析
                        </button>
                    </div>

                    {/* 说明信息 */}
                    <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                        <h4 className="font-medium text-blue-800 mb-2">分析说明：</h4>
                        <ul className="text-sm text-blue-700 space-y-1">
                            <li>• <strong>ChatGPT 智能分析：</strong>基于AI的深度分析，需要配置API Key</li>
                            <li>• <strong>本地规则分析：</strong>基于传统命理规则的分析，无需网络</li>
                            <li>• 分析结果仅供参考，不应作为重大决策的唯一依据</li>
                            <li>• 可以选择不同的分析类型获得针对性的解读</li>
                        </ul>
                    </div>
                </>
            ) : (
                <div className="space-y-6">
                    {/* 分析结果 */}
                    <div className="bg-white rounded-lg border border-gray-200 p-6">
                        <div className="flex items-center justify-between mb-4">
                            <h3 className="text-lg font-semibold text-gray-800">分析结果</h3>
                            <button
                                onClick={() => window.location.reload()}
                                className="text-sm text-primary-600 hover:text-primary-700"
                            >
                                重新分析
                            </button>
                        </div>

                        {analysisData.success ? (
                            <div className="space-y-4">
                                {/* 分析内容 */}
                                <div className="prose max-w-none">
                                    <pre className="whitespace-pre-wrap text-gray-700 leading-relaxed">
                                        {analysisData.data.analysis || analysisData.data.summary || '分析完成'}
                                    </pre>
                                </div>

                                {/* 关键点 */}
                                {analysisData.data.key_points && (
                                    <div>
                                        <h4 className="font-medium text-gray-800 mb-2">关键要点：</h4>
                                        <ul className="list-disc list-inside space-y-1 text-gray-700">
                                            {analysisData.data.key_points.map((point, index) => (
                                                <li key={index}>{point}</li>
                                            ))}
                                        </ul>
                                    </div>
                                )}

                                {/* 建议 */}
                                {analysisData.data.suggestions && (
                                    <div>
                                        <h4 className="font-medium text-gray-800 mb-2">建议：</h4>
                                        <ul className="list-disc list-inside space-y-1 text-gray-700">
                                            {analysisData.data.suggestions.map((suggestion, index) => (
                                                <li key={index}>{suggestion}</li>
                                            ))}
                                        </ul>
                                    </div>
                                )}

                                {/* 分析来源 */}
                                <div className="pt-4 border-t border-gray-200">
                                    <p className="text-sm text-gray-500">
                                        分析来源：{analysisData.source || '本地规则分析'} •
                                        置信度：{analysisData.data.confidence || '中等'}
                                    </p>
                                </div>
                            </div>
                        ) : (
                            <div className="text-center py-8">
                                <p className="text-red-600 mb-2">分析失败</p>
                                <p className="text-sm text-gray-500">{analysisData.message}</p>
                                {analysisData.data?.suggestions && (
                                    <div className="mt-4">
                                        <h4 className="font-medium text-gray-800 mb-2">建议：</h4>
                                        <ul className="text-sm text-gray-600 space-y-1">
                                            {analysisData.data.suggestions.map((suggestion, index) => (
                                                <li key={index}>• {suggestion}</li>
                                            ))}
                                        </ul>
                                    </div>
                                )}
                            </div>
                        )}
                    </div>
                </div>
            )}
        </div>
    );
};

export default AnalysisPanel; 