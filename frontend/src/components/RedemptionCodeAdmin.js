import React, { useState, useEffect } from 'react';
import { API_BASE } from '../config';
import { Plus, Trash2, Copy, RefreshCw, BarChart3 } from 'lucide-react';

function RedemptionCodeAdmin() {
    const [codes, setCodes] = useState([]);
    const [stats, setStats] = useState({});
    const [loading, setLoading] = useState(false);
    const [generateForm, setGenerateForm] = useState({
        quantity: 1,
        expires_in_days: 30
    });
    const [showCopyTip, setShowCopyTip] = useState('');

    // 获取兑换码列表
    const fetchCodes = async () => {
        setLoading(true);
        try {
            const response = await fetch(`${API_BASE}/api/redemption-codes/list`);
            if (response.ok) {
                const data = await response.json();
                setCodes(data);
            }
        } catch (error) {
            console.error('获取兑换码列表失败:', error);
        } finally {
            setLoading(false);
        }
    };

    // 获取统计信息
    const fetchStats = async () => {
        try {
            const response = await fetch(`${API_BASE}/api/redemption-codes/stats`);
            if (response.ok) {
                const data = await response.json();
                setStats(data);
            }
        } catch (error) {
            console.error('获取统计信息失败:', error);
        }
    };

    // 生成兑换码
    const generateCodes = async () => {
        setLoading(true);
        try {
            const response = await fetch(`${API_BASE}/api/redemption-codes/generate`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(generateForm)
            });

            if (response.ok) {
                const result = await response.json();
                alert(`成功生成 ${result.quantity} 个兑换码！`);
                fetchCodes();
                fetchStats();
            } else {
                const error = await response.json();
                alert(`生成失败: ${error.detail}`);
            }
        } catch (error) {
            console.error('生成兑换码失败:', error);
            alert('生成失败，请重试');
        } finally {
            setLoading(false);
        }
    };

    // 删除兑换码
    const deleteCode = async (code) => {
        if (!window.confirm(`确定要删除兑换码 ${code} 吗？`)) return;

        try {
            const response = await fetch(`${API_BASE}/api/redemption-codes/${code}`, {
                method: 'DELETE'
            });

            if (response.ok) {
                alert('删除成功');
                fetchCodes();
                fetchStats();
            } else {
                const error = await response.json();
                alert(`删除失败: ${error.detail}`);
            }
        } catch (error) {
            console.error('删除兑换码失败:', error);
            alert('删除失败，请重试');
        }
    };

    // 复制兑换码
    const copyCode = async (code) => {
        try {
            await navigator.clipboard.writeText(code);
            setShowCopyTip(code);
            setTimeout(() => setShowCopyTip(''), 2000);
        } catch (error) {
            console.error('复制失败:', error);
        }
    };

    // 格式化日期
    const formatDate = (dateString) => {
        return new Date(dateString).toLocaleString('zh-CN');
    };

    // 检查是否过期
    const isExpired = (expiresAt) => {
        return new Date(expiresAt) < new Date();
    };

    useEffect(() => {
        fetchCodes();
        fetchStats();
    }, []);

    return (
        <div className="min-h-screen bg-slate-900 text-slate-100 p-6">
            <div className="max-w-6xl mx-auto">
                {/* 页面标题 */}
                <div className="mb-8">
                    <h1 className="text-3xl font-bold text-slate-100 mb-2">兑换码管理</h1>
                    <p className="text-slate-400">管理AI报告兑换码的生成、查看和删除</p>
                </div>

                {/* 统计信息 */}
                <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
                    <div className="bg-slate-800 rounded-lg p-6 border border-slate-700">
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="text-slate-400 text-sm">总兑换码</p>
                                <p className="text-2xl font-bold text-slate-100">{stats.total_codes || 0}</p>
                            </div>
                            <BarChart3 className="w-8 h-8 text-blue-400" />
                        </div>
                    </div>
                    <div className="bg-slate-800 rounded-lg p-6 border border-slate-700">
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="text-slate-400 text-sm">已使用</p>
                                <p className="text-2xl font-bold text-red-400">{stats.used_codes || 0}</p>
                            </div>
                            <BarChart3 className="w-8 h-8 text-red-400" />
                        </div>
                    </div>
                    <div className="bg-slate-800 rounded-lg p-6 border border-slate-700">
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="text-slate-400 text-sm">可用</p>
                                <p className="text-2xl font-bold text-green-400">{stats.valid_codes || 0}</p>
                            </div>
                            <BarChart3 className="w-8 h-8 text-green-400" />
                        </div>
                    </div>
                    <div className="bg-slate-800 rounded-lg p-6 border border-slate-700">
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="text-slate-400 text-sm">使用率</p>
                                <p className="text-2xl font-bold text-purple-400">{stats.usage_rate || 0}%</p>
                            </div>
                            <BarChart3 className="w-8 h-8 text-purple-400" />
                        </div>
                    </div>
                </div>

                {/* 生成兑换码 */}
                <div className="bg-slate-800 rounded-lg p-6 border border-slate-700 mb-8">
                    <h2 className="text-xl font-semibold text-slate-100 mb-4">生成新兑换码</h2>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        <div>
                            <label className="block text-slate-300 text-sm mb-2">生成数量</label>
                            <input
                                type="number"
                                min="1"
                                max="100"
                                value={generateForm.quantity}
                                onChange={(e) => setGenerateForm(prev => ({ ...prev, quantity: parseInt(e.target.value) || 1 }))}
                                className="w-full bg-slate-700 border border-slate-600 text-slate-100 px-3 py-2 rounded-lg focus:border-blue-400 focus:ring-1 focus:ring-blue-400"
                            />
                        </div>
                        <div>
                            <label className="block text-slate-300 text-sm mb-2">有效期（天）</label>
                            <input
                                type="number"
                                min="1"
                                max="365"
                                value={generateForm.expires_in_days}
                                onChange={(e) => setGenerateForm(prev => ({ ...prev, expires_in_days: parseInt(e.target.value) || 30 }))}
                                className="w-full bg-slate-700 border border-slate-600 text-slate-100 px-3 py-2 rounded-lg focus:border-blue-400 focus:ring-1 focus:ring-blue-400"
                            />
                        </div>
                        <div className="flex items-end">
                            <button
                                onClick={generateCodes}
                                disabled={loading}
                                className="w-full bg-blue-500 text-white py-2 px-4 rounded-lg hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center justify-center"
                            >
                                {loading ? (
                                    <RefreshCw className="w-4 h-4 animate-spin mr-2" />
                                ) : (
                                    <Plus className="w-4 h-4 mr-2" />
                                )}
                                {loading ? '生成中...' : '生成兑换码'}
                            </button>
                        </div>
                    </div>
                </div>

                {/* 兑换码列表 */}
                <div className="bg-slate-800 rounded-lg border border-slate-700">
                    <div className="p-6 border-b border-slate-700">
                        <h2 className="text-xl font-semibold text-slate-100">兑换码列表</h2>
                    </div>
                    <div className="overflow-x-auto">
                        <table className="w-full">
                            <thead className="bg-slate-700/50">
                                <tr>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-slate-300 uppercase tracking-wider">兑换码</th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-slate-300 uppercase tracking-wider">状态</th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-slate-300 uppercase tracking-wider">创建时间</th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-slate-300 uppercase tracking-wider">使用时间</th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-slate-300 uppercase tracking-wider">过期时间</th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-slate-300 uppercase tracking-wider">操作</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-slate-700">
                                {loading ? (
                                    <tr>
                                        <td colSpan="6" className="px-6 py-4 text-center text-slate-400">
                                            <RefreshCw className="w-6 h-6 animate-spin mx-auto" />
                                            加载中...
                                        </td>
                                    </tr>
                                ) : codes.length === 0 ? (
                                    <tr>
                                        <td colSpan="6" className="px-6 py-4 text-center text-slate-400">
                                            暂无兑换码
                                        </td>
                                    </tr>
                                ) : (
                                    codes.map((code) => (
                                        <tr key={code.code} className="hover:bg-slate-700/30">
                                            <td className="px-6 py-4">
                                                <div className="flex items-center space-x-2">
                                                    <span className="font-mono text-slate-100">{code.code}</span>
                                                    <button
                                                        onClick={() => copyCode(code.code)}
                                                        className="p-1 hover:bg-slate-600 rounded text-slate-400 hover:text-slate-200"
                                                    >
                                                        <Copy className="w-4 h-4" />
                                                    </button>
                                                </div>
                                            </td>
                                            <td className="px-6 py-4">
                                                {code.is_used ? (
                                                    <span className="inline-flex px-2 py-1 text-xs font-semibold rounded-full bg-red-900/30 text-red-300">
                                                        已使用
                                                    </span>
                                                ) : isExpired(code.expires_at) ? (
                                                    <span className="inline-flex px-2 py-1 text-xs font-semibold rounded-full bg-gray-900/30 text-gray-300">
                                                        已过期
                                                    </span>
                                                ) : (
                                                    <span className="inline-flex px-2 py-1 text-xs font-semibold rounded-full bg-green-900/30 text-green-300">
                                                        可用
                                                    </span>
                                                )}
                                            </td>
                                            <td className="px-6 py-4 text-sm text-slate-300">
                                                {formatDate(code.created_at)}
                                            </td>
                                            <td className="px-6 py-4 text-sm text-slate-300">
                                                {code.used_at ? formatDate(code.used_at) : '-'}
                                            </td>
                                            <td className="px-6 py-4 text-sm text-slate-300">
                                                {formatDate(code.expires_at)}
                                            </td>
                                            <td className="px-6 py-4">
                                                <button
                                                    onClick={() => deleteCode(code.code)}
                                                    className="p-2 hover:bg-red-900/30 text-red-400 hover:text-red-300 rounded transition-colors"
                                                >
                                                    <Trash2 className="w-4 h-4" />
                                                </button>
                                            </td>
                                        </tr>
                                    ))
                                )}
                            </tbody>
                        </table>
                    </div>
                </div>

                {/* 复制提示 */}
                {showCopyTip && (
                    <div className="fixed bottom-4 right-4 bg-green-500 text-white px-4 py-2 rounded-lg shadow-lg animate-fade-in-out">
                        已复制兑换码: {showCopyTip}
                    </div>
                )}
            </div>
        </div>
    );
}

export default RedemptionCodeAdmin; 