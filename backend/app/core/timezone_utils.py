from timezonefinder import TimezoneFinder
from datetime import datetime
from typing import Dict, Any, Optional
from zoneinfo import ZoneInfo

def get_timezone_from_coordinates(longitude: float, latitude: float, at: Optional[datetime] = None) -> Dict[str, Any]:
    """
    根据经纬度获取时区信息

    Args:
        longitude: 经度
        latitude: 纬度
        at: 计算 UTC 偏移的时刻（应为出生时刻，naive 本地时间）。
            夏令时偏移随日期变化，用当前日期算历史出生的偏移会出错
            （如悉尼 5 月出生应为 +10，按 10 月底的今天算会得到 +11）。
            不传时退回当前时刻（仅供不关心历史偏移的调用方）。

    Returns:
        Dict containing timezone name and UTC offset (float 小时，可含 0.5)
    """
    try:
        tf = TimezoneFinder()
        timezone_str = tf.timezone_at(lat=latitude, lng=longitude)
        
        if timezone_str is None:
            # 如果无法确定时区，根据经度估算（更精确的计算）
            # 经度每15度对应1小时时差
            utc_offset = round(longitude / 15)
            # 限制在合理范围内 (-12 到 +14)
            utc_offset = max(-12, min(14, utc_offset))
            timezone_str = f"UTC{utc_offset:+d}"
            
            return {
                "timezone": timezone_str,
                "utc_offset": utc_offset,
                "estimated": True
            }
        
        # 在指定时刻（出生时刻）计算 UTC 偏移，保留半小时/三刻钟时区的精度
        tz = ZoneInfo(timezone_str)
        moment = at if at is not None else datetime.now()
        utc_offset = tz.utcoffset(moment).total_seconds() / 3600

        return {
            "timezone": timezone_str,
            "utc_offset": utc_offset,
            "estimated": False
        }
        
    except Exception as e:
        # fallback: 根据经度估算时区（更精确的计算）
        utc_offset = round(longitude / 15)
        utc_offset = max(-12, min(14, utc_offset))
        return {
            "timezone": f"UTC{utc_offset:+d}",
            "utc_offset": utc_offset,
            "estimated": True,
            "error": str(e)
        }

def format_timezone_offset(utc_offset: float) -> str:
    """
    将UTC偏移格式化为字符串

    Args:
        utc_offset: UTC偏移小时数（可带小数，如 5.5）

    Returns:
        格式化的时区字符串，如："+8", "-5", "+5.5"
        （下游 parse_input 用 float 解析，整数不带小数点以保持旧格式）
    """
    if utc_offset == int(utc_offset):
        return f"{int(utc_offset):+d}"
    return f"{utc_offset:+g}"

def get_location_info(longitude: float, latitude: float) -> Dict[str, Any]:
    """
    获取地理位置的详细信息
    
    Args:
        longitude: 经度
        latitude: 纬度
        
    Returns:
        包含时区和地理信息的字典
    """
    timezone_info = get_timezone_from_coordinates(longitude, latitude)
    
    # 简单的地理区域判断
    region = "未知地区"
    if 70 <= longitude <= 140 and 10 <= latitude <= 55:
        region = "亚洲"
    elif -180 <= longitude <= -50 and 10 <= latitude <= 80:
        region = "北美洲"
    elif -20 <= longitude <= 60 and 35 <= latitude <= 70:
        region = "欧洲"
    elif 110 <= longitude <= 180 and -50 <= latitude <= -10:
        region = "大洋洲"
    elif -80 <= longitude <= -35 and -60 <= latitude <= 15:
        region = "南美洲"
    elif -20 <= longitude <= 55 and -35 <= latitude <= 40:
        region = "非洲"
    
    return {
        **timezone_info,
        "region": region,
        "coordinates": {
            "longitude": longitude,
            "latitude": latitude
        }
    } 