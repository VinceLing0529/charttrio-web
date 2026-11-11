# 本地解读引擎测试

覆盖 `core/ziwei_patterns.py`（格局识别）、`core/shensha.py`（神煞）、
`api/analysis.py::_perform_local_analysis` 与 `/local-analysis` 端点。

```bash
cd backend
.venv/bin/pip install pytest   # 首次：venv 里默认没有 pytest
.venv/bin/python -m pytest tests/ -q
```

夹具：`conftest.py` —— Ling 真盘（1998-05-29 11:00 珠海，巳时，
手写夹具已与引擎实测输出对过）+ 1 个全手写合成盘 + 空/残缺/脏数据。
判定口径以 Renhuai123/ziwei-doushu 的 patterns.ts 原版为准。
