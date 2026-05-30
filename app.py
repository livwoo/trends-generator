import streamlit as st
from datetime import datetime
from pytrends.request import TrendReq
import feedparser
import requests
import warnings
warnings.filterwarnings("ignore")

st.set_page_config(page_title="內容選題生產器", page_icon="🎯", layout="wide")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@300;400;500;700&display=swap');
    html, body, [class*="css"] { font-family: 'Noto Sans TC', sans-serif; }
    .block-container { padding: 2rem 3rem; max-width: 1100px; }
    h1 { color: #ffffff; font-weight: 700; }
    .tag { display: inline-block; background: #1e1e1e; color: #a0a0a0; border: 1px solid #2e2e2e; border-radius: 20px; padding: 4px 14px; margin: 4px; font-size: 0.85rem; }
    .tag-hot { background: #1a1a2e; color: #7eb8f7; border-color: #2e4a6e; }
    .tag-rising { background: #1a2e1a; color: #7ef7a0; border-color: #2e6e3a; }
    .card { background: #1a1a1a; border: 1px solid #2a2a2a; border-radius: 12px; padding: 16px 20px; margin: 10px 0; }
    .metric-box { background: #1a1a1a; border: 1px solid #2a2a2a; border-radius: 10px; padding: 16px; text-align: center; }
    .metric-number { color: #7eb8f7; font-size: 1.6rem; font-weight: 700; }
    .metric-label { color: #666; font-size: 0.8rem; margin-top: 4px; }
    .divider { border: none; border-top: 1px solid #222; margin: 24px 0; }
    .hint { color: #444; font-size: 0.82rem; }
    .stButton > button { background: #ffffff; color: #000; border: none; border-radius: 8px; font-weight: 600; padding: 0.6rem 2rem; }
    .stTextInput > div > div > input { background: #1a1a1a; color: #fff; border: 1px solid #333; border-radius: 8px; }
</style>
""", unsafe_allow_html=True)

st.markdown("# 🎯 內容選題生產器")
st.markdown("<p style='color:#666;margin-top:-12px'>基於真實數據的內容切角靈感工具</p>", unsafe_allow_html=True)
st.markdown("<hr class='divider'>", unsafe_allow_html=True)


def fetch_trends(keyword):
    try:
        pt = TrendReq(hl="zh-TW", tz=480)
        pt.build_payload([keyword], timeframe="today 12-m", geo="TW")
        related = pt.related_queries()
        top, rising = [], []
        if keyword in related:
            if related[keyword]["top"] is not None:
                top = related[keyword]["top"]["query"].head(10).tolist()
            if related[keyword]["rising"] is not None:
                rising = related[keyword]["rising"]["query"].head(6).tolist()
        return {"top": top, "rising": rising}
    except Exception:
        return {"top": [], "rising": []}


def fetch_news(keyword, max_items=10):
    url = f"https://news.google.com/rss/search?q={requests.utils.quote(keyword)}&hl=zh-TW&gl=TW&ceid=TW:zh-Hant"
    try:
        feed = feedparser.parse(url)
        results = []
        for entry in feed.entries[:max_items]:
            pub = ""
            if hasattr(entry, "published"):
                try:
                    from email.utils import parsedate_to_datetime
                    pub = parsedate_to_datetime(entry.published).strftime("%Y-%m-%d")
                except Exception:
                    pub = entry.published[:10]
            results.append({
                "title": entry.get("title", ""),
                "source": entry.get("source", {}).get("title", ""),
                "url": entry.get("link", ""),
                "published": pub,
            })
        return results
    except Exception:
        return []


def build_report(keyword, trends, news):
    lines = [
        f"產業：{keyword}",
        f"日期：{datetime.now().strftime('%Y-%m-%d')}",
        f"地區：台灣｜時間範圍：近 12 個月",
        "",
        "=== Google Trends 台灣熱搜關鍵字 ===",
    ]
    for i, q in enumerate(trends.get("top", []), 1):
        lines.append(f"{i}. {q}")
    if trends.get("rising"):
        lines.append("\n急速上升關鍵字：")
        for q in trends["rising"]:
            lines.append(f"↑ {q}")

    lines += ["", "=== 近期台灣新聞熱點 ==="]
    for n in news:
        lines.append(f"• [{n['published']}] {n['title']}（{n['source']}）")

    lines += [
        "",
        "---",
        f"請根據以上數據，幫我生成 10 組「{keyword}」產業的內容切角。",
        "每組切角包含：標題方向、吸引力說明（為什麼這個切角有潛力）。",
        "優先考慮台灣受眾的搜尋習慣與時事熱點。",
    ]
    return "\n".join(lines)


# ── 輸入區 ────────────────────────────────────────────
col_in, col_btn = st.columns([4, 1])
with col_in:
    keyword = st.text_input("", placeholder="輸入產業關鍵字，例如：咖啡、健身、親子教育", label_visibility="collapsed")
with col_btn:
    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
    run = st.button("開始分析 →")

st.markdown("<p class='hint'>🌏 台灣地區｜⏱ 近 12 個月｜資料來源：Google Trends + Google 新聞</p>", unsafe_allow_html=True)

# ── 結果區 ────────────────────────────────────────────
if run and keyword:
    with st.spinner("正在抓取趨勢與新聞資料…"):
        trends = fetch_trends(keyword)
        news = fetch_news(keyword)

    st.markdown("<hr class='divider'>", unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f"<div class='metric-box'><div class='metric-number'>{len(trends.get('top', []))}</div><div class='metric-label'>熱搜關鍵字</div></div>", unsafe_allow_html=True)
    with c2:
        st.markdown(f"<div class='metric-box'><div class='metric-number'>{len(news)}</div><div class='metric-label'>近期新聞熱點</div></div>", unsafe_allow_html=True)

    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

    st.markdown("### 📈 Google Trends 台灣熱搜（近 12 個月）")
    if trends.get("top"):
        st.markdown("".join([f"<span class='tag tag-hot'>{q}</span>" for q in trends["top"]]), unsafe_allow_html=True)
    else:
        st.markdown("<p class='hint'>無資料</p>", unsafe_allow_html=True)

    if trends.get("rising"):
        st.markdown("<p class='hint' style='margin-top:14px'>急速上升</p>", unsafe_allow_html=True)
        st.markdown("".join([f"<span class='tag tag-rising'>↑ {q}</span>" for q in trends["rising"]]), unsafe_allow_html=True)

    st.markdown("<hr class='divider'>", unsafe_allow_html=True)

    st.markdown("### 🗞 近期台灣新聞熱點")
    if news:
        for n in news:
            st.markdown(f"""
            <div class='card'>
                <a href='{n['url']}' target='_blank' style='color:#fff;text-decoration:none;font-size:0.95rem;font-weight:500'>{n['title']}</a>
                <div class='hint' style='margin-top:6px'>{n['source']} · {n['published']}</div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.markdown("<p class='hint'>無法取得新聞資料</p>", unsafe_allow_html=True)

    st.markdown("<hr class='divider'>", unsafe_allow_html=True)

    st.markdown("### 📋 複製報告，貼給 Claude 生成切角")
    st.markdown("<p class='hint'>複製下方內容，貼到 Claude Code 對話框，直接得到 10 組切角建議</p>", unsafe_allow_html=True)
    st.code(build_report(keyword, trends, news), language=None)

elif run and not keyword:
    st.warning("請先輸入產業關鍵字")
