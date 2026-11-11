import json
import os

def test_qa_json():
    """测试QA结果JSON的有效性"""
    print("🔄 测试QA JSON有效性")
    print("=" * 50)
    
    # 读取QA结果文件
    qa_file = "data/reports/AI20250627182143vh78nvn2h/qa_result.json"
    if not os.path.exists(qa_file):
        print("❌ QA结果文件不存在")
        return
    
    try:
        with open(qa_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        print("✅ QA结果文件读取成功")
        print(f"📄 模块: {data.get('module')}")
        print(f"📄 订单号: {data.get('order_id')}")
        
        # 获取content字段
        content = data.get('content', '')
        print(f"📄 Content长度: {len(content)}")
        
        # 去掉```json```标记
        if content.startswith('```json'):
            content = content.replace('```json\n', '').replace('\n```', '')
            print("✅ 已去掉```json```标记")
        
        # 尝试解析JSON
        try:
            parsed_content = json.loads(content)
            print("✅ Content JSON解析成功")
            
            # 检查结构
            expected_keys = ['wealth_questions', 'career_questions', 'love_questions', 'personality_questions', 'fortune_questions']
            for key in expected_keys:
                if key in parsed_content:
                    questions = parsed_content[key]
                    print(f"✅ {key}: {len(questions)}个问题")
                else:
                    print(f"❌ 缺少 {key}")
                    
        except json.JSONDecodeError as e:
            print(f"❌ Content JSON解析失败: {e}")
            print(f"❌ 错误位置: 第{e.lineno}行, 第{e.colno}列")
            print(f"❌ 错误内容: {e.msg}")
            
            # 显示错误位置附近的内容
            lines = content.split('\n')
            if e.lineno <= len(lines):
                error_line = lines[e.lineno - 1]
                print(f"❌ 错误行内容: {error_line}")
                print(f"❌ 错误位置: {' ' * (e.colno - 1)}^")
            
    except Exception as e:
        print(f"❌ 文件读取失败: {e}")

if __name__ == "__main__":
    test_qa_json() 