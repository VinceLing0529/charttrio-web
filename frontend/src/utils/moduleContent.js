import { API_BASE } from '../config';

// 后端 module-data 返回的 content 是已解析的对象（AI 输出经后端 json.loads），
// 旧页面一律按 JSON 字符串处理，导致真实报告全部解析失败、回退到写死的模板文案。
// 这里统一兼容对象与字符串两种形态。
export function parseModuleContent(raw) {
    if (raw == null) return null;
    if (typeof raw === 'object') return raw;
    if (typeof raw === 'string') {
        let s = raw.trim();
        s = s.replace(/^```json\s*/i, '').replace(/^```\s*/, '').replace(/\s*```$/, '');
        try {
            return JSON.parse(s);
        } catch (e) {
            return null;
        }
    }
    return null;
}

export async function fetchModuleContent(orderId, module) {
    const response = await fetch(`${API_BASE}/api/ai-report/module-data/${orderId}/${module}`);
    if (!response.ok) {
        throw new Error(`Failed to load module data (${response.status})`);
    }
    const data = await response.json();
    const parsed = parseModuleContent(data.content);
    if (!parsed) {
        throw new Error('Could not parse module content');
    }
    return parsed;
}
