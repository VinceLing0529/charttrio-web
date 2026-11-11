"""命盘快照卡渲染：把 analysis 模块的大白话内容排成一张 1080x1440 宣纸风 PNG。

内容来源是报告自己的 plain_summary 字段（金句/盲区/长处/总结），不调用任何 AI。
字体依赖服务器的 Noto CJK（deploy/bootstrap.sh 安装 fonts-noto-cjk）；
找不到字体时抛 SnapshotFontError，由接口层转成 503。

语言由环境变量 SNAPSHOT_LANG 选择："en"（本英文站默认）或 "zh"（中文站文案）。
英文金句规则与中文站的「记住：」对应：blindspots 的 plain_summary 若以
"Remember:" 领起收尾句则按标记切分；没有标记时取最后一段完整句子作金句
（英文模板 v1.0.1 未强制标记，示例输出的收尾句即点题句）。
"""
import glob
import io
import os
import re

from PIL import Image, ImageDraw, ImageFont

PAPER = (246, 241, 231)
INK = (33, 29, 25)
CINNABAR = (179, 64, 42)
PINE = (51, 84, 77)
CHIP_BG = (227, 236, 228)
FAINT = (138, 129, 117)
LINE = (205, 196, 178)

W, H = 1080, 1440
X = 100
TEXT_W = W - 2 * X
FOOTER_LINE_Y = 1318

# 本树为英文站：默认 en。中文站保持 SNAPSHOT_LANG=zh（或在中文树里改默认值）。
LANG = os.environ.get("SNAPSHOT_LANG", "en").strip().lower()
if LANG not in ("en", "zh"):
    LANG = "en"

_STRINGS = {
    "zh": {
        "seal": "命",
        "brand": "生命洞察",
        "subtitle": "三盘合参 · 命盘报告",
        "chip": "我的命盘快照",
        "sec_blind": "命盘盲区",
        "sec_talents": "我的长处",
        "sec_summary": "一句话总结",
        "signature": "八字 · 紫微斗数 · 印度星盘",
        "footer": "生命洞察 · aimingpan.com",
        "incomplete": "报告内容不完整，无法生成快照",
        "jinju_font": 66,
        "jinju_step": 98,
        "budget_jinju": 36,
        "budget_blind": 92,
        "budget_talents": 72,
        "budget_summary": 72,
    },
    "en": {
        "seal": "命",
        "brand": "ChartTrio",
        "subtitle": "Three charts · One reading",
        "chip": "Your Chart Snapshot",
        "sec_blind": "Your Blind Spots",
        "sec_talents": "Your Natural Strengths",
        "sec_summary": "The Big Picture",
        "signature": "BaZi · Zi Wei Dou Shu · Vedic Astrology",
        "footer": "ChartTrio · charttrio.com",
        "incomplete": "Report content is incomplete; cannot build the snapshot card",
        "jinju_font": 58,
        "jinju_step": 92,
        "budget_jinju": 100,
        "budget_blind": 185,
        "budget_talents": 120,
        "budget_summary": 110,
    },
}


class SnapshotFontError(RuntimeError):
    pass


_font_cache = {}


def _find_font(kind: str, bold: bool):
    """kind: 'serif' | 'sans'. Returns a path or raises SnapshotFontError."""
    key = (kind, bold)
    if key in _font_cache:
        return _font_cache[key]
    weight = "Bold" if bold else "Regular"
    family = "NotoSerifCJK" if kind == "serif" else "NotoSansCJK"
    candidates = [
        f"/usr/share/fonts/opentype/noto/{family}-{weight}.ttc",
        f"/usr/share/fonts/truetype/noto/{family}-{weight}.ttc",
    ]
    extra_dir = os.environ.get("SNAPSHOT_FONT_DIR")
    if extra_dir:
        candidates = [os.path.join(extra_dir, f"{family}-{weight}.ttc")] + candidates
    for path in candidates:
        if os.path.exists(path):
            _font_cache[key] = path
            return path
    # glob fallback: any Noto CJK of the family, then any CJK font at all
    patterns = [
        f"/usr/share/fonts/**/{family}*.ttc",
        f"/usr/share/fonts/**/{family}*.otf",
        "/usr/share/fonts/**/*CJK*.ttc",
        "/usr/share/fonts/**/*CJK*.otf",
    ]
    for pat in patterns:
        hits = sorted(glob.glob(pat, recursive=True))
        bold_hits = [h for h in hits if "Bold" in h]
        if hits:
            path = (bold_hits[0] if bold and bold_hits else hits[0])
            _font_cache[key] = path
            return path
    raise SnapshotFontError(f"CJK font not found: {family}-{weight}")


def _font(kind, bold, size):
    return ImageFont.truetype(_find_font(kind, bold), size)


def _plain(content: dict, section: str) -> str:
    node = content.get(section) or {}
    if isinstance(node, dict):
        return (node.get("plain_summary") or "").strip()
    return ""


def _sentences_en(text: str):
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", text.strip()) if s.strip()]


def extract_highlights(content: dict, lang: str = LANG) -> dict:
    """从 analysis content 提取快照文案：金句 + 盲区/长处/总结三段大白话。"""
    blind = _plain(content, "blindspots")
    talents = _plain(content, "talents")
    summary = _plain(content, "summary")

    jinju = ""
    blind_body = blind
    if lang == "en":
        # 英文版「记住：」等价规则：优先 "Remember:" 标记切分
        for marker in ("Remember:", "Remember："):
            if marker in blind:
                blind_body, _, tail = blind.partition(marker)
                jinju = tail.strip().rstrip(".")
                blind_body = blind_body.strip().rstrip(";. ")
                break
        if not jinju:
            # 模板未强制标记时：blindspots 的收尾句即点题金句，摘出来作标题
            sents = _sentences_en(blind)
            if len(sents) >= 2:
                jinju = sents[-1].rstrip(".")
                blind_body = " ".join(sents[:-1])
            if not jinju and summary:
                jinju = _sentences_en(summary)[0].rstrip(".")
        return {"jinju": jinju, "blind": blind_body, "talents": talents, "summary": summary}

    for marker in ("记住：", "记住:"):
        if marker in blind:
            blind_body, _, tail = blind.partition(marker)
            jinju = tail.strip().rstrip("。")
            blind_body = blind_body.strip().rstrip("；。")
            break
    if not jinju and summary:
        jinju = summary.split("。")[0].strip()
    return {"jinju": jinju, "blind": blind_body, "talents": talents, "summary": summary}


def _truncate(text: str, budget: int) -> str:
    text = " ".join(text.split())
    if len(text) <= budget:
        return text
    cut = text[:budget]
    # 尽量断在标点处
    for sep in ("；", "，", "。", "、"):
        idx = cut.rfind(sep)
        if idx > budget * 0.55:
            return cut[: idx + (1 if sep in ("；", "。") else 0)].rstrip("，、") + ("…" if sep in ("，", "、") else "")
    return cut + "…"


def _truncate_en(text: str, budget: int) -> str:
    text = " ".join(text.split())
    if len(text) <= budget:
        return text
    cut = text[:budget]
    # 尽量断在句子/分句边界处
    for sep in (". ", "; ", ", "):
        idx = cut.rfind(sep)
        if idx > budget * 0.55:
            if sep == ". ":
                return cut[: idx + 1].strip()
            return cut[:idx].rstrip(",; ") + "…"
    return cut.rstrip() + "…"


def _wrap(draw, text, font, max_w):
    lines, cur = [], ""
    for ch in text:
        if ch == "\n":
            lines.append(cur)
            cur = ""
            continue
        if draw.textlength(cur + ch, font=font) <= max_w:
            cur += ch
        else:
            lines.append(cur)
            cur = ch
    if cur:
        lines.append(cur)
    return lines


def _wrap_en(draw, text, font, max_w):
    """英文按词换行；单个词超宽时退回逐字切分。"""
    lines, cur = [], ""
    for word in text.split(" "):
        if not word:
            continue
        trial = f"{cur} {word}" if cur else word
        if draw.textlength(trial, font=font) <= max_w:
            cur = trial
            continue
        if cur:
            lines.append(cur)
        if draw.textlength(word, font=font) <= max_w:
            cur = word
        else:
            parts = _wrap(draw, word, font, max_w)
            lines.extend(parts[:-1])
            cur = parts[-1] if parts else ""
    if cur:
        lines.append(cur)
    return lines


def render_snapshot_png(content: dict, lang: str = LANG) -> bytes:
    s = _STRINGS[lang]
    trunc = _truncate_en if lang == "en" else _truncate
    wrap = _wrap_en if lang == "en" else _wrap
    hl = extract_highlights(content, lang)
    if not hl["jinju"] and not hl["blind"]:
        raise ValueError(s["incomplete"])

    img = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(img)

    # ---- header ----
    d.rounded_rectangle([72, 72, 164, 164], radius=18, fill=CINNABAR)
    d.text((118, 118), s["seal"], font=_font("serif", True, 58), fill=(255, 255, 255), anchor="mm")
    d.text((190, 92), s["brand"], font=_font("serif", True, 54), fill=INK)
    d.text((192, 160), s["subtitle"], font=_font("serif", False, 29), fill=FAINT)

    # ---- chip ----
    chip_font = _font("sans", True, 33)
    label = s["chip"]
    tw = d.textlength(label, font=chip_font)
    d.rounded_rectangle([72, 238, 72 + tw + 44, 300], radius=31, fill=CHIP_BG)
    d.text((94, 269), label, font=chip_font, fill=PINE, anchor="lm")

    y = 356

    # ---- 金句 ----
    if hl["jinju"]:
        jf = _font("serif", True, s["jinju_font"])
        # 金句过长时按标点截断并加省略号，避免三行硬切在半句话上
        jinju_text = trunc(hl["jinju"], s["budget_jinju"])
        for ln in wrap(d, jinju_text, jf, TEXT_W):
            if y > 640:
                break
            d.text((X, y), ln, font=jf, fill=INK)
            y += s["jinju_step"]
        y += 34

    # ---- sections ----
    body_font = _font("serif", False, 39)
    head_font = _font("sans", True, 36)
    sections = [
        (s["sec_blind"], trunc(hl["blind"], s["budget_blind"])),
        (s["sec_talents"], trunc(hl["talents"], s["budget_talents"])),
    ]
    for title, text in sections:
        if not text or y > FOOTER_LINE_Y - 190:
            continue
        d.rectangle([X, y + 8, X + 10, y + 44], fill=CINNABAR)
        d.text((X + 24, y), title, font=head_font, fill=PINE)
        y += 58
        for ln in wrap(d, text, body_font, TEXT_W):
            if y > FOOTER_LINE_Y - 70:
                break
            d.text((X, y), ln, font=body_font, fill=INK)
            y += 60
        y += 36

    # 一句总结：放得下才放（整段放不下宁可不放，不截半段）
    summary_text = trunc(hl["summary"], s["budget_summary"])
    if summary_text:
        s_lines = wrap(d, summary_text, body_font, TEXT_W)
        if y + 58 + len(s_lines) * 60 <= FOOTER_LINE_Y - 40:
            d.rectangle([X, y + 8, X + 10, y + 44], fill=CINNABAR)
            d.text((X + 24, y), s["sec_summary"], font=head_font, fill=PINE)
            y += 58
            for ln in s_lines:
                d.text((X, y), ln, font=body_font, fill=INK)
                y += 60
            y += 36

    # 底部留白较多时，补一行三盘签名（与卡片组的页脚呼应）
    if y < FOOTER_LINE_Y - 170:
        d.text((W / 2, FOOTER_LINE_Y - 108), s["signature"], font=_font("serif", False, 34), fill=FAINT, anchor="mm")

    # ---- footer ----
    d.line([72, FOOTER_LINE_Y, W - 72, FOOTER_LINE_Y], fill=LINE, width=2)
    d.text((W / 2, 1364), s["footer"], font=_font("serif", False, 29), fill=FAINT, anchor="mm")

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()
