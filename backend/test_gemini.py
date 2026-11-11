import os
import requests
import json

# 配置Gemini API
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "AIzaSyCW-fBuUTOReZR6cRewSGVE6j4K3rZfyd8")
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"

def test_gemini_api():
    """测试Gemini API是否正常工作"""
    try:
        headers = {
            'Content-Type': 'application/json'
        }
        
        data = {
            "contents": [
                {
                    "parts": [
                        {
                            "text": "你好，请简单介绍一下自己。"
                        }
                    ]
                }
            ]
        }
        
        # 添加API密钥到URL
        url = f"{GEMINI_API_URL}?key={GEMINI_API_KEY}"
        
        print(f"正在测试Gemini API...")
        print(f"URL: {url}")
        print(f"API Key: {GEMINI_API_KEY[:10]}...")
        
        # 增加超时时间到60秒
        response = requests.post(url, headers=headers, json=data, timeout=60)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"Success! Response: {json.dumps(result, indent=2, ensure_ascii=False)}")
            
            if 'candidates' in result and len(result['candidates']) > 0:
                content = result['candidates'][0]['content']['parts'][0]['text']
                print(f"Generated Content: {content}")
                return True
            else:
                print("API返回格式错误")
                return False
        else:
            print(f"API请求失败: {response.status_code} - {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print("Gemini API调用超时")
        return False
    except Exception as e:
        print(f"Gemini API调用错误: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_gemini_api()
    if success:
        print("✅ Gemini API测试成功")
    else:
        print("❌ Gemini API测试失败") 