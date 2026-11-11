import json

def test_specific_order():
    """测试特定订单AI202506280503472jpffcgkm的QA JSON格式"""
    print("🔄 测试订单AI202506280503472jpffcgkm的QA JSON格式")
    print("=" * 60)
    
    # 读取特定订单的QA结果文件
    qa_file = "data/reports/AI202506280503472jpffcgkm/qa_result.json"
    
    try:
        with open(qa_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        print("✅ QA结果文件读取成功")
        print(f"📄 订单号: {data.get('order_id')}")
        print(f"📄 模块: {data.get('module')}")
        
        # 获取content字段
        content = data.get('content', '')
        print(f"📄 Content长度: {len(content)}")
        print(f"📄 Content是否包含```json: {content.startswith('```json')}")
        
        # 前端的处理逻辑
        if '```json' in content:
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
                            print(f"  ✅ 问题{i+1}: {q['question'][:30]}...")
                        else:
                            print(f"  ❌ 问题{i+1}: 缺少question或answer字段")
                            print(f"  📄 实际内容: {q}")
                else:
                    print(f"❌ 缺少 {key}")
                    
        except json.JSONDecodeError as e:
            print(f"❌ Content JSON解析失败: {e}")
            print(f"❌ 错误位置: 第{e.lineno}行, 第{e.colno}列")
            print(f"❌ 错误内容: {e.msg}")
            
            # 显示错误位置附近的内容
            lines = content.split('\n')
            if e.lineno <= len(lines):
                start_line = max(0, e.lineno - 3)
                end_line = min(len(lines), e.lineno + 2)
                print(f"❌ 错误位置附近的内容:")
                for i in range(start_line, end_line):
                    marker = ">>> " if i == e.lineno - 1 else "    "
                    print(f"{marker}第{i+1}行: {lines[i]}")
                    
            # 显示第3002个字符附近的内容
            if len(content) > 3002:
                start_pos = max(0, 3002 - 50)
                end_pos = min(len(content), 3002 + 50)
                print(f"❌ 第3002个字符附近的内容:")
                print(f"'{content[start_pos:end_pos]}'")
                print(f"                                                  ^")
                
    except Exception as e:
        print(f"❌ 文件读取失败: {e}")

if __name__ == "__main__":
    test_specific_order() 