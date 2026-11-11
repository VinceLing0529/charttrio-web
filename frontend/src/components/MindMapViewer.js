import React, { useEffect, useRef } from 'react';
import mermaid from 'mermaid';
import { Map, RefreshCw } from 'lucide-react';
import LoadingSpinner from './LoadingSpinner';

const MindMapViewer = ({ data, onGenerate, loading }) => {
    const mermaidRef = useRef(null);

    useEffect(() => {
        if (data && data.mindmap && mermaidRef.current) {
            // 初始化 Mermaid
            mermaid.initialize({
                startOnLoad: true,
                theme: 'default',
                mindmap: {
                    padding: 20,
                    maxNodeSize: 200
                },
                themeVariables: {
                    primaryColor: '#ee5a24',
                    primaryTextColor: '#fff',
                    primaryBorderColor: '#ee5a24',
                    lineColor: '#374151',
                    sectionBkgColor: '#f9fafb',
                    altSectionBkgColor: '#ffffff',
                    gridColor: '#e5e7eb',
                    secondaryColor: '#0ea5e9',
                    tertiaryColor: '#d946ef'
                }
            });

            // 渲染思维导图
            const renderMindmap = async () => {
                try {
                    const { svg } = await mermaid.render('mindmap-chart', data.mindmap);
                    mermaidRef.current.innerHTML = svg;
                } catch (error) {
                    console.error('Mermaid渲染失败:', error);
                    mermaidRef.current.innerHTML = `
            <div class="text-center py-8 text-red-600">
              <p>思维导图渲染失败</p>
              <p class="text-sm text-gray-500 mt-2">${error.message}</p>
            </div>
          `;
                }
            };

            renderMindmap();
        }
    }, [data]);

    if (loading) {
        return (
            <div className="mindmap-container min-h-[400px] flex items-center justify-center">
                <LoadingSpinner text="正在生成思维导图..." />
            </div>
        );
    }

    if (!data) {
        return (
            <div className="mindmap-container min-h-[400px] flex flex-col items-center justify-center">
                <div className="text-center">
                    <Map className="w-16 h-16 text-gray-300 mx-auto mb-4" />
                    <h3 className="text-lg font-medium text-gray-700 mb-2">暂无思维导图</h3>
                    <p className="text-gray-500 mb-6">点击下方按钮生成命理分析思维导图</p>
                    <button
                        onClick={onGenerate}
                        className="btn-primary flex items-center"
                    >
                        <Map className="w-4 h-4 mr-2" />
                        生成思维导图
                    </button>
                </div>
            </div>
        );
    }

    return (
        <div className="space-y-4">
            {/* 工具栏 */}
            <div className="flex justify-between items-center">
                <div>
                    <h3 className="text-lg font-semibold text-gray-800">命理分析思维导图</h3>
                    <p className="text-sm text-gray-600">三盘融合分析的可视化展示</p>
                </div>

                <button
                    onClick={onGenerate}
                    disabled={loading}
                    className="btn-outline flex items-center"
                >
                    <RefreshCw className="w-4 h-4 mr-2" />
                    重新生成
                </button>
            </div>

            {/* 思维导图容器 */}
            <div className="mindmap-container min-h-[500px]">
                <div
                    ref={mermaidRef}
                    className="w-full h-full flex items-center justify-center"
                />
            </div>

            {/* 说明信息 */}
            <div className="bg-gray-50 rounded-lg p-4">
                <h4 className="font-medium text-gray-800 mb-2">思维导图说明：</h4>
                <ul className="text-sm text-gray-600 space-y-1">
                    <li>• 中心节点为命理分析总览</li>
                    <li>• 三个主分支分别代表八字、紫微斗数、印度星盘</li>
                    <li>• 各分支下展示相应系统的关键信息</li>
                    <li>• 颜色编码对应不同的命理系统</li>
                </ul>
            </div>
        </div>
    );
};

export default MindMapViewer; 