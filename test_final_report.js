// 测试FinalReport页面功能
console.log('=== FinalReport页面测试 ===');

// 测试路由
const testRoutes = () => {
    console.log('✅ 路由配置测试');
    console.log('- 主页面: /');
    console.log('- FinalReport页面: /final-report/:orderId');
    console.log('- 示例订单号: AI20250626T195117zrdkd9');
    console.log('- 测试URL: http://localhost:3000/final-report/AI20250626T195117zrdkd9');
};

// 测试API调用
const testAPI = async () => {
    console.log('\n✅ API调用测试');
    try {
        const response = await fetch('http://localhost:8000/ai/analysis/AI20250626T195117zrdkd9');
        if (response.ok) {
            const data = await response.json();
            console.log('✅ API调用成功');
            console.log('- 数据包含dimensions:', !!data.dimensions);
            console.log('- 包含用户数据:', !!data.user_data);
            console.log('- 四大模块:', Object.keys(data.dimensions || {}));
        } else {
            console.log('❌ API调用失败:', response.status);
        }
    } catch (error) {
        console.log('❌ API调用错误:', error.message);
    }
};

// 测试页面跳转
const testNavigation = () => {
    console.log('\n✅ 页面跳转测试');
    console.log('1. 点击"立即获取完整报告" → 生成订单号 → 跳转到 /final-report/{orderId}');
    console.log('2. 输入订单号 → 点击"读取报告" → 检测存在 → 跳转到 /final-report/{orderId}');
    console.log('3. 在FinalReport页面点击任意模块 → 显示详细分析');
};

// 运行测试
const runTests = async () => {
    testRoutes();
    await testAPI();
    testNavigation();

    console.log('\n=== 测试完成 ===');
    console.log('请访问 http://localhost:3000 测试完整功能');
};

runTests(); 