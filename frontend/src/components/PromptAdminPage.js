import React, { useState, useEffect } from 'react';
import { API_BASE } from '../config';
import { useNavigate } from 'react-router-dom';
import { ArrowLeft, Save, RotateCcw, Eye, Code, FileText, Settings } from 'lucide-react';

const PromptAdminPage = () => {
    const navigate = useNavigate();
    const [prompts, setPrompts] = useState([]);
    const [selectedPrompt, setSelectedPrompt] = useState(null);
    const [editingContent, setEditingContent] = useState('');
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [previewData, setPreviewData] = useState(null);
    const [showPreview, setShowPreview] = useState(false);

    useEffect(() => {
        loadPrompts();
    }, []);

    const loadPrompts = async () => {
        try {
            setLoading(true);
            const response = await fetch(`${API_BASE}/api/prompt-admin/prompts`);
            if (response.ok) {
                const data = await response.json();
                setPrompts(data);
                if (data.length > 0) {
                    setSelectedPrompt(data[0]);
                    setEditingContent(data[0].content);
                }
            }
        } catch (error) {
            console.error('加载prompts失败:', error);
        } finally {
            setLoading(false);
        }
    };

    const handlePromptSelect = (prompt) => {
        setSelectedPrompt(prompt);
        setEditingContent(prompt.content);
        setShowPreview(false);
    };

    const handleSave = async () => {
        if (!selectedPrompt) return;

        try {
            setSaving(true);
            const response = await fetch(`${API_BASE}/api/prompt-admin/prompts/${selectedPrompt.name}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    content: editingContent,
                    version: selectedPrompt.version
                })
            });

            if (response.ok) {
                const result = await response.json();
                // 更新本地状态
                setSelectedPrompt(result.prompt);
                setPrompts(prompts.map(p =>
                    p.name === selectedPrompt.name ? result.prompt : p
                ));
                alert('保存成功！');
            } else {
                throw new Error('保存失败');
            }
        } catch (error) {
            console.error('保存失败:', error);
            alert('保存失败，请重试');
        } finally {
            setSaving(false);
        }
    };

    const handleReset = async () => {
        if (!selectedPrompt) return;

        if (!window.confirm('确定要重置到默认值吗？这将丢失所有修改。')) {
            return;
        }

        try {
            setSaving(true);
            const response = await fetch(`${API_BASE}/api/prompt-admin/prompts/${selectedPrompt.name}/reset`, {
                method: 'POST'
            });

            if (response.ok) {
                const result = await response.json();
                setSelectedPrompt(result.prompt);
                setEditingContent(result.prompt.content);
                setPrompts(prompts.map(p =>
                    p.name === selectedPrompt.name ? result.prompt : p
                ));
                alert('重置成功！');
            } else {
                throw new Error('重置失败');
            }
        } catch (error) {
            console.error('重置失败:', error);
            alert('重置失败，请重试');
        } finally {
            setSaving(false);
        }
    };

    const handlePreview = async () => {
        if (!selectedPrompt) return;

        try {
            const response = await fetch(`${API_BASE}/api/prompt-admin/prompts/${selectedPrompt.name}/preview`);
            if (response.ok) {
                const data = await response.json();
                setPreviewData(data);
                setShowPreview(true);
            }
        } catch (error) {
            console.error('预览失败:', error);
            alert('预览失败，请重试');
        }
    };

    const getPromptIcon = (name) => {
        switch (name) {
            case 'analysis': return '📊';
            case 'mindmap': return '⭐';
            case 'fortune': return '🔮';
            case 'qa': return '💡';
            default: return '📝';
        }
    };

    const getPromptColor = (name) => {
        switch (name) {
            case 'analysis': return 'from-blue-500 to-cyan-500';
            case 'mindmap': return 'from-amber-500 to-orange-500';
            case 'fortune': return 'from-purple-500 to-pink-500';
            case 'qa': return 'from-emerald-500 to-teal-500';
            default: return 'from-gray-500 to-gray-600';
        }
    };

    if (loading) {
        return (
            <div className="min-h-screen bg-gradient-to-br from-slate-900 via-gray-900 to-slate-800 flex items-center justify-center">
                <div className="text-center">
                    <div className="w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
                    <p className="text-slate-300">加载中...</p>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-gradient-to-br from-slate-900 via-gray-900 to-slate-800">
            {/* Header */}
            <div className="flex items-center justify-between p-6 bg-slate-800/80 backdrop-blur-sm border-b border-slate-700">
                <div className="flex items-center gap-4">
                    <button
                        onClick={() => navigate('/')}
                        className="p-2 rounded-lg bg-slate-700/50 hover:bg-slate-600/50 transition-colors"
                    >
                        <ArrowLeft className="w-5 h-5 text-slate-300" />
                    </button>
                    <div>
                        <h1 className="text-xl font-semibold text-white">AI提示词管理</h1>
                        <p className="text-slate-400 text-sm">调整四个AI分析模块的提示词模板</p>
                    </div>
                </div>
            </div>

            <div className="flex h-[calc(100vh-88px)]">
                {/* 左侧Prompt列表 */}
                <div className="w-80 bg-slate-800/50 border-r border-slate-700 p-4 overflow-y-auto">
                    <h2 className="text-lg font-semibold text-white mb-4">提示词模板</h2>
                    <div className="space-y-3">
                        {prompts.map((prompt) => (
                            <div
                                key={prompt.name}
                                onClick={() => handlePromptSelect(prompt)}
                                className={`p-4 rounded-lg cursor-pointer transition-all duration-300 ${selectedPrompt?.name === prompt.name
                                    ? 'bg-gradient-to-r ' + getPromptColor(prompt.name) + ' text-white'
                                    : 'bg-slate-700/50 hover:bg-slate-600/50 text-slate-300'
                                    }`}
                            >
                                <div className="flex items-center gap-3">
                                    <span className="text-2xl">{getPromptIcon(prompt.name)}</span>
                                    <div className="flex-1">
                                        <h3 className="font-semibold">{prompt.title}</h3>
                                        <p className="text-sm opacity-80">{prompt.description}</p>
                                        <p className="text-xs opacity-60 mt-1">版本: {prompt.version}</p>
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>

                {/* 右侧编辑区域 */}
                <div className="flex-1 flex flex-col">
                    {selectedPrompt ? (
                        <>
                            {/* 工具栏 */}
                            <div className="p-4 border-b border-slate-700 bg-slate-800/50">
                                <div className="flex items-center justify-between">
                                    <div className="flex items-center gap-3">
                                        <span className="text-2xl">{getPromptIcon(selectedPrompt.name)}</span>
                                        <div>
                                            <h2 className="text-lg font-semibold text-white">{selectedPrompt.title}</h2>
                                            <p className="text-slate-400 text-sm">最后修改: {new Date(selectedPrompt.last_modified).toLocaleString()}</p>
                                        </div>
                                    </div>
                                    <div className="flex items-center gap-2">
                                        <button
                                            onClick={handlePreview}
                                            className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors"
                                        >
                                            <Eye className="w-4 h-4" />
                                            预览
                                        </button>
                                        <button
                                            onClick={handleReset}
                                            disabled={saving}
                                            className="flex items-center gap-2 px-4 py-2 bg-orange-600 hover:bg-orange-700 disabled:bg-gray-600 text-white rounded-lg transition-colors"
                                        >
                                            <RotateCcw className="w-4 h-4" />
                                            重置
                                        </button>
                                        <button
                                            onClick={handleSave}
                                            disabled={saving}
                                            className="flex items-center gap-2 px-4 py-2 bg-green-600 hover:bg-green-700 disabled:bg-gray-600 text-white rounded-lg transition-colors"
                                        >
                                            <Save className="w-4 h-4" />
                                            {saving ? '保存中...' : '保存'}
                                        </button>
                                    </div>
                                </div>
                            </div>

                            {/* 编辑区域 */}
                            <div className="flex-1 flex">
                                {showPreview && previewData ? (
                                    <div className="flex-1 flex">
                                        {/* 原始内容 */}
                                        <div className="flex-1 p-4">
                                            <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                                                <Code className="w-5 h-5" />
                                                原始模板
                                            </h3>
                                            <textarea
                                                value={editingContent}
                                                onChange={(e) => setEditingContent(e.target.value)}
                                                className="w-full h-full p-4 bg-slate-800 border border-slate-600 rounded-lg text-slate-200 font-mono text-sm resize-none focus:outline-none focus:ring-2 focus:ring-blue-500"
                                                placeholder="输入提示词模板..."
                                            />
                                        </div>

                                        {/* 预览内容 */}
                                        <div className="flex-1 p-4 border-l border-slate-700">
                                            <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                                                <FileText className="w-5 h-5" />
                                                预览效果
                                            </h3>
                                            <div className="w-full h-full p-4 bg-slate-800 border border-slate-600 rounded-lg text-slate-200 font-mono text-sm overflow-auto">
                                                <pre className="whitespace-pre-wrap">{previewData.formatted_content}</pre>
                                            </div>
                                        </div>
                                    </div>
                                ) : (
                                    <div className="flex-1 p-4">
                                        <textarea
                                            value={editingContent}
                                            onChange={(e) => setEditingContent(e.target.value)}
                                            className="w-full h-full p-4 bg-slate-800 border border-slate-600 rounded-lg text-slate-200 font-mono text-sm resize-none focus:outline-none focus:ring-2 focus:ring-blue-500"
                                            placeholder="输入提示词模板..."
                                        />
                                    </div>
                                )}
                            </div>
                        </>
                    ) : (
                        <div className="flex-1 flex items-center justify-center">
                            <div className="text-center">
                                <Settings className="w-16 h-16 text-slate-400 mx-auto mb-4" />
                                <p className="text-slate-400">请选择一个提示词模板进行编辑</p>
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

export default PromptAdminPage; 