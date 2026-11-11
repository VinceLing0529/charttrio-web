import axios from 'axios';
import { API_BASE } from '../config';

// 创建axios实例（baseURL 走 config 的 API_BASE：生产构建注入空串 → 同源相对路径；
// 不能用 || 'http://localhost:8000'，空串是 falsy 会被吞掉，导致线上包仍指向 localhost）
const api = axios.create({
    baseURL: API_BASE,
    timeout: 30000,
    headers: {
        'Content-Type': 'application/json',
    },
});

// 请求拦截器
api.interceptors.request.use(
    (config) => {
        console.log('API Request:', config.method?.toUpperCase(), config.url);
        return config;
    },
    (error) => {
        console.error('API Request Error:', error);
        return Promise.reject(error);
    }
);

// 响应拦截器
api.interceptors.response.use(
    (response) => {
        console.log('API Response:', response.status, response.config.url);
        return response;
    },
    (error) => {
        console.error('API Response Error:', error.response?.status, error.response?.data);
        return Promise.reject(error);
    }
);

// API服务类
class ApiService {
    // 健康检查
    async healthCheck() {
        try {
            const response = await api.get('/health');
            return response.data;
        } catch (error) {
            throw new Error(`Health check failed: ${error.message}`);
        }
    }

    // 获取时区信息
    async getTimezone(longitude, latitude) {
        try {
            const response = await api.get('/api/timezone', {
                params: { longitude, latitude }
            });
            return response.data;
        } catch (error) {
            throw new Error(`Timezone lookup failed: ${error.response?.data?.detail || error.message}`);
        }
    }

    // 计算三盘命盘
    async calculateCharts(birthInfo) {
        try {
            const response = await api.post('/api/charts/calculate', birthInfo);
            if (response.data.success) {
                return response.data.data;
            } else {
                throw new Error(response.data.message || 'Calculation failed');
            }
        } catch (error) {
            if (error.response?.data?.detail) {
                throw new Error(error.response.data.detail);
            } else if (error.response?.data?.message) {
                throw new Error(error.response.data.message);
            } else {
                throw new Error(`Chart calculation failed: ${error.message}`);
            }
        }
    }

    // 仅计算八字
    async calculateBaziOnly(birthInfo) {
        try {
            const response = await api.post('/api/charts/bazi-only', birthInfo);
            if (response.data.success) {
                return response.data.data;
            } else {
                throw new Error(response.data.message || 'BaZi calculation failed');
            }
        } catch (error) {
            throw new Error(`BaZi calculation failed: ${error.response?.data?.detail || error.message}`);
        }
    }

    // 仅计算紫微斗数
    async calculateZiweiOnly(birthInfo) {
        try {
            const response = await api.post('/api/charts/ziwei-only', birthInfo);
            if (response.data.success) {
                return response.data.data;
            } else {
                throw new Error(response.data.message || 'Zi Wei calculation failed');
            }
        } catch (error) {
            throw new Error(`Zi Wei calculation failed: ${error.response?.data?.detail || error.message}`);
        }
    }

    // 仅计算印度星盘
    async calculateVedicOnly(birthInfo) {
        try {
            const response = await api.post('/api/charts/vedic-only', birthInfo);
            if (response.data.success) {
                return response.data.data;
            } else {
                throw new Error(response.data.message || 'Vedic chart calculation failed');
            }
        } catch (error) {
            throw new Error(`Vedic chart calculation failed: ${error.response?.data?.detail || error.message}`);
        }
    }

    // ChatGPT分析
    async analyzeWithChatGPT(chartData, analysisType, customQuestion = '') {
        try {
            const response = await api.post('/api/analysis/chatgpt', {
                chart_data: chartData,
                analysis_type: analysisType,
                custom_question: customQuestion
            });
            return response.data;
        } catch (error) {
            throw new Error(`Analysis failed: ${error.response?.data?.detail || error.message}`);
        }
    }

    // 生成思维导图
    async generateMindmap(chartData, focusArea = 'comprehensive') {
        try {
            const response = await api.post('/api/analysis/mindmap', {
                chart_data: chartData,
                focus_area: focusArea
            });
            if (response.data.success) {
                return response.data.data;
            } else {
                throw new Error(response.data.message || 'Mind map generation failed');
            }
        } catch (error) {
            throw new Error(`Mind map generation failed: ${error.response?.data?.detail || error.message}`);
        }
    }

    // 本地分析
    async localAnalysis(chartData, analysisType) {
        try {
            const response = await api.post('/api/analysis/local-analysis', {
                chart_data: chartData,
                analysis_type: analysisType
            });
            if (response.data.success) {
                return response.data.data;
            } else {
                throw new Error(response.data.message || 'Local analysis failed');
            }
        } catch (error) {
            throw new Error(`Local analysis failed: ${error.response?.data?.detail || error.message}`);
        }
    }

    // 生成AI报告
    async generateAIReport(userData) {
        try {
            const response = await api.post('/api/ai-report/generate', {
                user_data: userData
            });
            return response.data;
        } catch (error) {
            throw new Error(`Report generation failed: ${error.response?.data?.detail || error.message}`);
        }
    }

    // 通过订单号获取历史报告
    async getReportByOrderId(orderId) {
        try {
            const response = await api.get(`/api/ai-report/report/${orderId}`);
            return response.data;
        } catch (error) {
            if (error.response?.status === 404) {
                throw new Error('Order ID not found — please check it and try again');
            }
            throw new Error(`Failed to load the report: ${error.response?.data?.detail || error.message}`);
        }
    }

    // 查询订单状态
    async getOrderStatus(orderId) {
        try {
            const response = await api.get(`/api/ai-report/status/${orderId}`);
            return response.data;
        } catch (error) {
            if (error.response?.status === 404) {
                throw new Error('Order ID not found');
            }
            throw new Error(`Failed to check order status: ${error.response?.data?.detail || error.message}`);
        }
    }

    // 列出所有报告（管理用）
    async listAllReports() {
        try {
            const response = await api.get('/api/ai-report/reports/list');
            return response.data;
        } catch (error) {
            throw new Error(`Failed to load the report list: ${error.response?.data?.detail || error.message}`);
        }
    }
}

// 创建并导出实例
const apiService = new ApiService();
export default apiService;

// AI分析相关API
export const aiAnalysisAPI = {
    // 批量生成分析 - 直接传入用户数据
    async batchGenerate(userData, orderId) {
        try {
            const response = await api.post('/api/ai-report/generate', {
                user_data: userData,
                order_id: orderId
            });
            return response.data;
        } catch (error) {
            console.error('Batch analysis failed:', error);
            throw new Error(error.response?.data?.detail || 'Batch analysis failed');
        }
    },

    // 原有的单独API（兼容性保留）
    async generateDimensionAnalysis(dimensionId, birthData, orderId) {
        try {
            const response = await api.post('/api/ai-report/dimension', {
                dimension_id: dimensionId,
                birth_data: birthData,
                order_id: orderId
            });
            return response.data;
        } catch (error) {
            console.error('Dimension analysis failed:', error);
            throw new Error(error.response?.data?.detail || 'Dimension analysis failed');
        }
    },

    async generateComprehensiveAnalysis(dimensionResults, birthData, orderId) {
        try {
            const response = await api.post('/api/ai-report/comprehensive', {
                dimension_results: dimensionResults,
                birth_data: birthData,
                order_id: orderId
            });
            return response.data;
        } catch (error) {
            console.error('Summary analysis failed:', error);
            throw new Error(error.response?.data?.detail || 'Summary analysis failed');
        }
    },

    async getSavedAnalysis(orderId) {
        try {
            const response = await api.get(`/api/ai-report/report/${orderId}`);
            return response.data;
        } catch (error) {
            if (error.response?.status === 404) {
                throw new Error('No analysis result found');
            }
            console.error('Failed to load the analysis result:', error);
            throw new Error(error.response?.data?.detail || 'Failed to load the analysis result');
        }
    }
};

// 新增API函数（全部改为相对路径）
export const generateSingleModule = async (orderId, module) => {
    try {
        const response = await fetch(`/api/ai-report/generate-module`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                order_id: orderId,
                module: module
            })
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        return await response.json();
    } catch (error) {
        console.error('生成单个模块失败:', error);
        throw error;
    }
};

export const getModuleStatus = async (orderId) => {
    try {
        const response = await fetch(`/api/ai-report/module-status/${orderId}`);

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        return await response.json();
    } catch (error) {
        console.error('获取模块状态失败:', error);
        throw error;
    }
};

export const getModuleData = async (orderId, module) => {
    try {
        const response = await fetch(`/api/ai-report/module-data/${orderId}/${module}`);

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        return await response.json();
    } catch (error) {
        console.error('获取模块数据失败:', error);
        throw error;
    }
};

export const simulateProgress = async (orderId, module) => {
    try {
        const response = await fetch(`/api/ai-report/simulate-progress/${orderId}/${module}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        return await response.json();
    } catch (error) {
        console.error('模拟进度失败:', error);
        throw error;
    }
}; 