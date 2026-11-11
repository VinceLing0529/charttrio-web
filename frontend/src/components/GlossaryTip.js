import React, { useCallback, useEffect, useRef, useState } from 'react';
import { createPortal } from 'react-dom';
import { GLOSSARY } from '../data/glossary';

// 同一时间只允许一个解释卡打开：打开新的时通知其余的关闭
let currentOpenId = null;
const openListeners = new Set();
function broadcastOpen(id) {
    currentOpenId = id;
    openListeners.forEach((fn) => fn(id));
}

// 盘面元素大白话解释卡。
// 用法：<GlossaryTip k="daymaster:丙">丙</GlossaryTip>
// - 桌面：鼠标悬停 / 键盘聚焦显示；移动端：点按切换。
// - 弹层用 fixed 定位（portal 到 body），按触发元素的位置就近摆放并做视口夹取，
//   不会被四柱表格的 overflow 容器裁剪。
// - 词条查不到时静默降级为纯文本，不影响原有渲染。
const GlossaryTip = ({ k, children, className = '' }) => {
    const entry = k ? GLOSSARY[k] : null;
    const idRef = useRef(null);
    if (idRef.current === null) {
        idRef.current = `gt-${Math.random().toString(36).slice(2, 9)}`;
    }
    const triggerRef = useRef(null);
    const openedAtRef = useRef(0);
    const [box, setBox] = useState(null); // {left, width, top} 或 {left, width, bottom}

    const hide = useCallback(() => {
        setBox(null);
        if (currentOpenId === idRef.current) broadcastOpen(null);
    }, []);

    const show = useCallback(() => {
        const el = triggerRef.current;
        if (!el) return;
        const r = el.getBoundingClientRect();
        const vw = window.innerWidth;
        const vh = window.innerHeight;
        const width = Math.min(288, vw - 24);
        let left = r.left + r.width / 2 - width / 2;
        left = Math.max(12, Math.min(left, vw - width - 12));
        // 下方空间不足（约 < 210px）且上方更宽裕时改到上方弹出
        if (r.bottom + 210 > vh && r.top > 220) {
            setBox({ left, width, bottom: vh - r.top + 8 });
        } else {
            setBox({ left, width, top: r.bottom + 8 });
        }
        openedAtRef.current = Date.now();
        broadcastOpen(idRef.current);
    }, []);

    // 别的词条被打开时关闭自己
    useEffect(() => {
        const fn = (openId) => {
            if (openId !== idRef.current) setBox(null);
        };
        openListeners.add(fn);
        return () => openListeners.delete(fn);
    }, []);

    // 打开期间：滚动/缩放直接关闭（避免弹层与元素错位）；点到触发元素与弹层之外关闭
    useEffect(() => {
        if (!box) return undefined;
        const onScrollOrResize = () => hide();
        const onDocPointerDown = (e) => {
            if (triggerRef.current && triggerRef.current.contains(e.target)) return;
            hide();
        };
        window.addEventListener('scroll', onScrollOrResize, true);
        window.addEventListener('resize', onScrollOrResize);
        document.addEventListener('pointerdown', onDocPointerDown, true);
        return () => {
            window.removeEventListener('scroll', onScrollOrResize, true);
            window.removeEventListener('resize', onScrollOrResize);
            document.removeEventListener('pointerdown', onDocPointerDown, true);
        };
    }, [box, hide]);

    if (!entry) return <>{children}</>;

    const handleClick = (e) => {
        // 结果页卡片整体有点击展开/收起逻辑，词条的点按不能冒泡触发它
        e.stopPropagation();
        // 移动端点按会先合成一次 mouseenter 把卡打开（openedAt 刚刷新），
        // 400ms 内的这次 click 视为「打开」而非「关闭」，避免一触即关
        if (box && Date.now() - openedAtRef.current > 400) {
            hide();
        } else {
            show();
        }
    };

    return (
        <>
            <span
                ref={triggerRef}
                role="button"
                tabIndex={0}
                aria-label={`${entry.title} — tap for the plain-words explanation`}
                className={`cursor-pointer border-b border-dotted border-primary-500/60 hover:text-primary-700 focus:outline-none focus:text-primary-700 ${className}`}
                onMouseEnter={show}
                onMouseLeave={hide}
                onFocus={show}
                onBlur={hide}
                onClick={handleClick}
                onKeyDown={(e) => {
                    if (e.key === 'Enter' || e.key === ' ') {
                        e.preventDefault();
                        e.stopPropagation();
                        if (box) hide(); else show();
                    }
                }}
            >
                {children}
            </span>
            {box && createPortal(
                <div
                    className="fixed z-[999] rounded border border-line bg-paper-card p-3.5 shadow-soft text-left font-sans pointer-events-none"
                    style={{ left: box.left, width: box.width, top: box.top, bottom: box.bottom }}
                >
                    <p className="font-serif font-bold text-ink text-sm mb-1 pl-2 border-l-2 border-primary-600">
                        {entry.title}
                    </p>
                    <p className="text-[13px] leading-relaxed text-ink-soft font-normal">{entry.text}</p>
                </div>,
                document.body
            )}
        </>
    );
};

export default GlossaryTip;
