import React, { useState } from 'react';
import RedemptionCodeAdmin from './RedemptionCodeAdmin';
import PromptAdminPage from './PromptAdminPage';

const ADMIN_USER = '729270660';
const ADMIN_PASS = 'Lingw123';

function ManageAdminPage() {
    const [loggedIn, setLoggedIn] = useState(false);
    const [form, setForm] = useState({ username: '', password: '' });
    const [error, setError] = useState('');
    const [tab, setTab] = useState('redemption');

    const handleLogin = async (e) => {
        e.preventDefault();
        setError('');
        try {
            const res = await fetch('/api/manage-admin/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(form)
            });
            if (res.ok) {
                setLoggedIn(true);
            } else {
                setError('账号或密码错误');
            }
        } catch (err) {
            setError('网络错误');
        }
    };

    if (!loggedIn) {
        return (
            <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-900 via-gray-900 to-slate-800">
                <form onSubmit={handleLogin} className="bg-slate-800 p-8 rounded-xl shadow-lg w-80 border border-slate-700">
                    <h2 className="text-2xl font-bold text-slate-100 mb-6 text-center">管理后台登录</h2>
                    <div className="mb-4">
                        <label className="block text-slate-300 mb-1">账号</label>
                        <input type="text" className="w-full px-3 py-2 rounded bg-slate-700 text-slate-100 border border-slate-600 focus:outline-none" value={form.username} onChange={e => setForm(f => ({ ...f, username: e.target.value }))} />
                    </div>
                    <div className="mb-4">
                        <label className="block text-slate-300 mb-1">密码</label>
                        <input type="password" className="w-full px-3 py-2 rounded bg-slate-700 text-slate-100 border border-slate-600 focus:outline-none" value={form.password} onChange={e => setForm(f => ({ ...f, password: e.target.value }))} />
                    </div>
                    {error && <div className="text-red-400 mb-2 text-sm">{error}</div>}
                    <button type="submit" className="w-full bg-blue-500 hover:bg-blue-600 text-white py-2 rounded-lg font-semibold">登录</button>
                </form>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-slate-900 text-slate-100">
            <div className="flex items-center justify-between p-6 bg-slate-800/80 border-b border-slate-700">
                <h1 className="text-2xl font-bold">管理后台</h1>
                <button onClick={() => setLoggedIn(false)} className="bg-slate-700 px-4 py-1 rounded-lg text-slate-300 hover:bg-slate-600">退出登录</button>
            </div>
            <div className="max-w-6xl mx-auto p-6">
                <div className="flex gap-4 mb-6">
                    <button onClick={() => setTab('redemption')} className={`px-6 py-2 rounded-t-lg font-semibold ${tab === 'redemption' ? 'bg-blue-500 text-white' : 'bg-slate-700 text-slate-300'}`}>兑换码管理</button>
                    <button onClick={() => setTab('prompt')} className={`px-6 py-2 rounded-t-lg font-semibold ${tab === 'prompt' ? 'bg-blue-500 text-white' : 'bg-slate-700 text-slate-300'}`}>AI提示词管理</button>
                </div>
                <div className="bg-slate-800 rounded-b-lg p-6 border border-slate-700">
                    {tab === 'redemption' && <RedemptionCodeAdmin />}
                    {tab === 'prompt' && <PromptAdminPage />}
                </div>
            </div>
        </div>
    );
}

export default ManageAdminPage; 