import json

def test_deepseek_qa():
    """测试DeepSeek完整QA文件"""
    print("🔄 测试DeepSeek完整QA文件")
    print("=" * 50)
    
    # 读取DeepSeek QA结果文件
    qa_file = "data/reports/AI20250627182143vh78nvn2h/qa_result_deepseek.json"
    
    try:
        with open(qa_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        print("✅ DeepSeek QA结果文件读取成功")
        
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
                    
                    # 检查每个问题的结构
                    for i, q in enumerate(questions):
                        if 'question' in q and 'answer' in q:
                            print(f"  ✅ 问题{i+1}: {q['question'][:20]}...")
                        else:
                            print(f"  ❌ 问题{i+1}: 缺少question或answer字段")
                else:
                    print(f"❌ 缺少 {key}")
                    
        except json.JSONDecodeError as e:
            print(f"❌ Content JSON解析失败: {e}")
            print(f"❌ 错误位置: 第{e.lineno}行, 第{e.colno}列")
            print(f"❌ 错误内容: {e.msg}")
            
    except Exception as e:
        print(f"❌ 文件读取失败: {e}")

if __name__ == "__main__":
    test_deepseek_qa() 