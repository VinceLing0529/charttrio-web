// 后端 API 基础地址：构建时由 REACT_APP_API_URL 注入，本地开发默认 8000 端口。
// 历史上多个组件把 http://localhost:8000 写死在 fetch 里，部署到任何非本地域名都会失效，统一走这里。
// 生产同源部署时显式传空串（REACT_APP_API_URL=）→ 走相对路径，由反向代理转发 /api。
const _envUrl = process.env.REACT_APP_API_URL;
export const API_BASE = _envUrl !== undefined ? _envUrl : 'http://localhost:8000';
