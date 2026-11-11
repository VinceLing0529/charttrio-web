from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Dict, Any, List
import copy
import json
import os
from pathlib import Path
from datetime import datetime

router = APIRouter()

# 配置存储目录：锚定到仓库内的 backend/data/prompts（模板的唯一事实来源），
# 不再随启动目录漂移——旧实现是相对路径，从 backend/ 启动和从 backend/app 启动
# 会读到两套不同的模板，管理页的修改也可能写进无人读取的影子目录。
_env_prompts = os.environ.get("PROMPTS_DIR", "").strip()
PROMPTS_DIR = Path(_env_prompts) if _env_prompts else Path(__file__).resolve().parents[2] / "data" / "prompts"
PROMPTS_DIR.mkdir(parents=True, exist_ok=True)

class PromptTemplate(BaseModel):
    name: str
    title: str
    description: str
    content: str
    version: str
    last_modified: str

class PromptUpdateRequest(BaseModel):
    content: str = Field(..., min_length=1)  # 禁止把线上模板清空（恢复默认可救，但先拦住）
    version: str

# 默认的prompt模板
DEFAULT_PROMPTS = {
    "analysis": {"name": "analysis", "version": "0.0.0", "content": "模板未配置：正式模板存放在服务器私有目录（环境变量 PROMPTS_DIR 指向），不随公开仓库分发。请基于以下命盘数据做简要分析。"},
    "mindmap": {"name": "mindmap", "version": "0.0.0", "content": "模板未配置：正式模板存放在服务器私有目录（环境变量 PROMPTS_DIR 指向），不随公开仓库分发。"},
    "fortune": {"name": "fortune", "version": "0.0.0", "content": "模板未配置：正式模板存放在服务器私有目录（环境变量 PROMPTS_DIR 指向），不随公开仓库分发。"},
    "qa": {"name": "qa", "version": "0.0.0", "content": "模板未配置：正式模板存放在服务器私有目录（环境变量 PROMPTS_DIR 指向），不随公开仓库分发。"},
}

def load_prompt_template(prompt_name: str) -> Dict[str, Any]:
    """加载prompt模板"""
    prompt_file = PROMPTS_DIR / f"{prompt_name}.json"
    
    if prompt_file.exists():
        try:
            with open(prompt_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"加载prompt模板失败: {str(e)}")
    
    # 如果文件不存在或加载失败，返回默认模板。
    # 必须深拷贝：调用方（PUT 更新）会原地修改返回的 dict，直接返回
    # DEFAULT_PROMPTS 本体等于把"出厂默认"在进程内永久改掉（实测踩过）。
    return copy.deepcopy(DEFAULT_PROMPTS.get(prompt_name, {}))

def save_prompt_template(prompt_name: str, prompt_data: Dict[str, Any]) -> bool:
    """保存prompt模板"""
    try:
        prompt_file = PROMPTS_DIR / f"{prompt_name}.json"
        with open(prompt_file, 'w', encoding='utf-8') as f:
            json.dump(prompt_data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"保存prompt模板失败: {str(e)}")
        return False

@router.get("/prompts")
async def get_all_prompts() -> List[PromptTemplate]:
    """获取所有prompt模板"""
    prompts = []
    for prompt_name in ["analysis", "mindmap", "fortune", "qa"]:
        prompt_data = load_prompt_template(prompt_name)
        if prompt_data:
            prompts.append(PromptTemplate(**prompt_data))
    return prompts

@router.get("/prompts/{prompt_name}")
async def get_prompt_template(prompt_name: str) -> PromptTemplate:
    """获取指定的prompt模板"""
    prompt_data = load_prompt_template(prompt_name)
    if not prompt_data:
        raise HTTPException(status_code=404, detail="Prompt template not found")
    return PromptTemplate(**prompt_data)

@router.put("/prompts/{prompt_name}")
async def update_prompt_template(prompt_name: str, request: PromptUpdateRequest) -> Dict[str, Any]:
    """更新prompt模板"""
    prompt_data = load_prompt_template(prompt_name)
    if not prompt_data:
        raise HTTPException(status_code=404, detail="Prompt template not found")
    
    # 更新内容
    prompt_data["content"] = request.content
    prompt_data["version"] = request.version
    prompt_data["last_modified"] = datetime.now().isoformat()
    
    # 保存到文件
    if save_prompt_template(prompt_name, prompt_data):
        return {"message": "Prompt template updated successfully", "prompt": prompt_data}
    else:
        raise HTTPException(status_code=500, detail="Failed to save prompt template")

@router.post("/prompts/{prompt_name}/reset")
async def reset_prompt_template(prompt_name: str) -> Dict[str, Any]:
    """重置prompt模板到默认值"""
    if prompt_name not in DEFAULT_PROMPTS:
        raise HTTPException(status_code=404, detail="Prompt template not found")
    
    default_prompt = DEFAULT_PROMPTS[prompt_name].copy()
    default_prompt["last_modified"] = datetime.now().isoformat()
    
    if save_prompt_template(prompt_name, default_prompt):
        return {"message": "Prompt template reset successfully", "prompt": default_prompt}
    else:
        raise HTTPException(status_code=500, detail="Failed to reset prompt template")

@router.get("/prompts/{prompt_name}/preview")
async def preview_prompt_template(prompt_name: str) -> Dict[str, Any]:
    """预览prompt模板（包含示例数据）"""
    prompt_data = load_prompt_template(prompt_name)
    if not prompt_data:
        raise HTTPException(status_code=404, detail="Prompt template not found")
    
    # 示例数据
    sample_data = {
        "gender_str": "男",
        "birth_date": "1995-06-15",
        "birth_time": "14:30",
        "true_solar_time": "14:25",
        "location_name": "上海市",
        "longitude": "121.5",
        "latitude": "31.2",
        "timezone": "+8",
        "bazi_year_pillar": "乙亥",
        "bazi_month_pillar": "己巳",
        "bazi_day_pillar": "丁酉",
        "bazi_hour_pillar": "丁未",
        "bazi_day_master": "丁",
        "bazi_body_strength": "身弱",
        "bazi_five_elements": '{"金": 2, "木": 1, "水": 1, "火": 3, "土": 1}',
        "bazi_ten_gods": '{"年干": "偏印", "月干": "食神", "日干": "日主", "时干": "比肩"}',
        "bazi_enhanced_analysis": "详细的八字分析内容...",
        "ziwei_lunar_date": "农历二月十五",
        "ziwei_chinese_date": "乙亥年 己巳月 丁酉日",
        "ziwei_soul": "丁火",
        "ziwei_body": "酉金",
        "ziwei_palaces_detail": "紫微斗数十二宫详析...",
        "ziwei_lu": "禄存",
        "ziwei_quan": "权星",
        "ziwei_ke": "科星",
        "ziwei_ji": "忌星",
        "vedic_chart_type": "Vedic Chart",
        "vedic_ayanamsa_type": "Koch Coordinates",
        "vedic_ayanamsa_value": "23.45°",
        "vedic_ascendant_sign": "Aries",
        "vedic_ascendant_lon": "20°",
        "vedic_planets_detail": "行星位置详析...",
        "vedic_axis_points_detail": "重要轴点分析...",
        "current_month": "January 2025",
        "prediction_start": "February 2025",
        "prediction_end": "January 2026",
        "prediction_months": ["February 2025", "March 2025", "April 2025", "May 2025", "June 2025", "July 2025", "August 2025", "September 2025", "October 2025", "November 2025", "December 2025", "January 2026"],
        # 添加可能用到的JSON结构变量
        "summary": '{"title": "命理综述", "overview": "整体命理特征概述示例"}',
        "talents": '{"title": "天赋优势", "overview": "天赋优势总体分析示例"}',
        "tensions": '{"title": "内心张力", "overview": "内心张力特征总体分析示例"}',
        "blindspots": '{"title": "命盘盲区", "overview": "潜在盲区总体分析示例"}',
        "guidance": '{"title": "成长引导", "overview": "成长路径总体分析示例"}',
        "positive_traits": '{"overview": "正向性格特征的总体分析示例", "details": []}',
        "negative_tendencies": '{"overview": "负向性格倾向的总体分析示例", "details": []}',
        "conflicting_aspects": '{"overview": "潜在冲突性格的总体分析示例", "details": []}',
        "strength_areas": '{"overview": "易发展领域的总体分析示例", "details": []}',
        "weakness_areas": '{"overview": "易出问题领域的总体分析示例", "details": []}',
        "monthly_predictions": '[{"month": "February 2025", "career_score": 8, "wealth_score": 7, "relationship_score": 9, "health_score": 8}]',
        "career_questions": '[{"question": "我适合从事什么行业？", "answer": "基于命理的详细分析和职业建议"}]',
        "relationship_questions": '[{"question": "我的感情特质是什么？", "answer": "从命理角度看，您的感情特质是..."}]',
        "wealth_questions": '[{"question": "我的财运特点是什么？", "answer": "基于命理的详细分析和理财建议"}]',
        "health_questions": '[{"question": "我需要注意哪些健康问题？", "answer": "从命理角度，您需要注意..."}]',
        "life_questions": '[{"question": "我的人生使命是什么？", "answer": "根据您的命理特征，您的人生使命是..."}]'
    }
    # 自动展开prediction_months
    if "prediction_months" in sample_data and isinstance(sample_data["prediction_months"], list):
        for i, v in enumerate(sample_data["prediction_months"]):
            sample_data[f"prediction_month_{i}"] = v
    
    # 格式化prompt内容
    try:
        formatted_content = prompt_data["content"].format(**sample_data)
    except KeyError as e:
        formatted_content = f"模板格式化错误: 缺少变量 {e}"
    
    return {
        "prompt_name": prompt_name,
        "original_content": prompt_data["content"],
        "formatted_content": formatted_content,
        "sample_data": sample_data
    } 