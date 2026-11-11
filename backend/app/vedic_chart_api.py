#!/usr/bin/env python3
"""
增强版印度星盘API
基于flatlib库，支持恒星历（sidereal）模式，使用Lahiri ayanamsa
"""

import json
import argparse
from typing import Dict, Any
from flatlib import const
from flatlib.datetime import Datetime
from flatlib.geopos import GeoPos
from flatlib.chart import Chart

def get_vedic_chart(date: str, time: str, tz: str, lat: float, lon: float) -> Dict[str, Any]:
    """
    计算印度星盘（恒星历模式）
    
    Args:
        date: 日期 (YYYY-MM-DD 格式)
        time: 时间 (HH:MM 格式)  
        tz: 时区 (+HH:MM 或 +H 格式，如 +08:00 或 +8)
        lat: 纬度
        lon: 经度
        
    Returns:
        包含恒星历星盘信息的字典，包括：
        - 上升点的 sign、house、lon
        - 10颗主行星的 sign、house、lon（如果可用）
        - 所有度数保留两位小数
        - 使用Lahiri ayanamsa恒星历系统
    """
    
    try:
        # 格式化时区
        if len(tz) == 2:  # +8 -> +08:00
            tz = tz + ':00'
        elif len(tz) == 3 and tz[1:].isdigit():  # +8 -> +08:00
            tz = tz[0] + '0' + tz[1:] + ':00'
        
        # 创建flatlib对象
        date_str = date.replace('-', '/')  # 转换为 YYYY/MM/DD 格式
        flatlib_dt = Datetime(date_str, time + ':00', tz)
        
        # 创建地理位置（需要转换为度分格式）
        lat_deg = int(abs(lat))
        lat_min = int((abs(lat) - lat_deg) * 60)
        lat_str = f"{lat_deg}{'n' if lat >= 0 else 's'}{lat_min:02d}"
        
        lon_deg = int(abs(lon))
        lon_min = int((abs(lon) - lon_deg) * 60)
        lon_str = f"{lon_deg}{'e' if lon >= 0 else 'w'}{lon_min:02d}"
        
        geo_pos = GeoPos(lat_str, lon_str)
        
        # 定义需要的行星和关键点常量和名称映射
        planet_map = {
            # 主要行星
            const.SUN: "Sun",
            const.MOON: "Moon", 
            const.MERCURY: "Mercury",
            const.VENUS: "Venus",
            const.MARS: "Mars",
            const.JUPITER: "Jupiter",
            const.SATURN: "Saturn",
            # 月亮交点
            const.NORTH_NODE: "North Node",  # 拉胡
            const.SOUTH_NODE: "South Node",  # 凯图
        }
        
        # 外行星和其他重要点（如果可用）
        try:
            planet_map.update({
                const.URANUS: "Uranus",
                const.NEPTUNE: "Neptune", 
                const.PLUTO: "Pluto"
            })
        except:
            pass
        
        # 重要轴点（如果可用）
        axis_points = {}
        try:
            axis_points.update({
                const.DESC: "Descendant",        # 下降点
                const.MC: "Midheaven",          # 天顶
                const.IC: "Imum Coeli",         # 天底
                const.PARS_FORTUNA: "Pars Fortuna"  # 福点
            })
        except:
            pass
        
        # 创建星盘
        chart = Chart(flatlib_dt, geo_pos)
        
        # 计算Lahiri Ayanamsa值（根据年份动态调整）
        year = int(date[:4])
        # 1900年Lahiri ayanamsa约为22.46度，每年增加约0.0139度
        lahiri_ayanamsa = 22.46 + (year - 1900) * 0.0139
        
        result = {
            "chart_type": "vedic_sidereal",
            "ayanamsa": {
                "type": "lahiri",
                "value": round(lahiri_ayanamsa, 2)
            },
            "input": {
                "date": date,
                "time": time,
                "timezone": tz,
                "latitude": lat,
                "longitude": lon
            },
            "ascendant": {},
            "planets": {},
            "axis_points": {}
        }
        
        # 星座名称
        signs = [
            "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
            "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"
        ]
        
        # 获取上升点信息
        asc = chart.get(const.ASC)
        if asc:
            # 应用恒星历修正
            tropical_lon = asc.lon
            sidereal_lon = (tropical_lon - lahiri_ayanamsa) % 360
            
            # 计算恒星历星座
            sidereal_sign_index = int(sidereal_lon // 30)
            sidereal_sign_degree = sidereal_lon % 30
            
            result["ascendant"] = {
                "sign": signs[sidereal_sign_index],
                "house": 1,  # 上升点总是在第1宫
                "lon": round(sidereal_sign_degree, 2)
            }
        
        # 获取行星信息
        for planet_const, planet_name in planet_map.items():
            try:
                obj = chart.get(planet_const)
                if obj:
                    # 应用恒星历修正
                    tropical_lon = obj.lon
                    sidereal_lon = (tropical_lon - lahiri_ayanamsa) % 360
                    
                    # 计算恒星历星座
                    sidereal_sign_index = int(sidereal_lon // 30)
                    sidereal_sign_degree = sidereal_lon % 30
                    
                    # 计算宫位（基于恒星历上升点）
                    if asc:
                        asc_sidereal_lon = (asc.lon - lahiri_ayanamsa) % 360
                        house_offset = ((sidereal_lon - asc_sidereal_lon) % 360) // 30
                        house = int(house_offset) + 1
                    else:
                        house = 1
                    
                    result["planets"][planet_name] = {
                        "sign": signs[sidereal_sign_index],
                        "house": house,
                        "lon": round(sidereal_sign_degree, 2)
                    }
                    
            except Exception as e:
                # 如果某个行星获取失败，跳过但不影响其他行星
                print(f"警告：无法获取 {planet_name} 的信息: {e}")
                continue
        
        # 获取轴点信息（下降点、天顶、天底、福点等）
        for axis_const, axis_name in axis_points.items():
            try:
                obj = chart.get(axis_const)
                if obj:
                    # 应用恒星历修正
                    tropical_lon = obj.lon
                    sidereal_lon = (tropical_lon - lahiri_ayanamsa) % 360
                    
                    # 计算恒星历星座
                    sidereal_sign_index = int(sidereal_lon // 30)
                    sidereal_sign_degree = sidereal_lon % 30
                    
                    # 计算宫位（基于恒星历上升点）
                    if asc:
                        asc_sidereal_lon = (asc.lon - lahiri_ayanamsa) % 360
                        house_offset = ((sidereal_lon - asc_sidereal_lon) % 360) // 30
                        house = int(house_offset) + 1
                    else:
                        house = 1
                    
                    result["axis_points"][axis_name] = {
                        "sign": signs[sidereal_sign_index],
                        "house": house,
                        "lon": round(sidereal_sign_degree, 2)
                    }
                    
            except Exception as e:
                # 如果某个轴点获取失败，跳过但不影响其他轴点
                print(f"警告：无法获取 {axis_name} 的信息: {e}")
                continue
        
        return result
        
    except Exception as e:
        return {
            "error": f"印度星盘计算错误: {str(e)}",
            "chart_type": "vedic_sidereal",
            "note": "请检查输入参数格式"
        }

def main():
    """命令行接口"""
    parser = argparse.ArgumentParser(description="增强版印度星盘计算器")
    parser.add_argument("--date", required=True, help="出生日期 (YYYY-MM-DD)")
    parser.add_argument("--time", required=True, help="出生时间 (HH:MM)")
    parser.add_argument("--timezone", required=True, help="时区 (+8 或 +08:00)")
    parser.add_argument("--latitude", type=float, required=True, help="纬度")
    parser.add_argument("--longitude", type=float, required=True, help="经度")
    
    args = parser.parse_args()
    
    result = get_vedic_chart(
        date=args.date,
        time=args.time,
        tz=args.timezone,
        lat=args.latitude,
        lon=args.longitude
    )
    
    print(json.dumps(result, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main() 