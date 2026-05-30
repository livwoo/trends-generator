import streamlit as st
from datetime import datetime, timedelta
from googleapiclient.discovery import build
from pytrends.request import TrendReq
import feedparser
import requests
import re
import warnings
warnings.filterwarnings("ignore")

YOUTUBE_API_KEY = st.secrets.get("YOUTUBE_API_KEY", "")

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
    .card-kol { background: #1a1a24; border: 1px solid #2a2a3e; border-radius: 12px; padding: 16px 20px; margin: 10px 0; }
    .badge-red { display: inline-block; background: #2e1a1a; color: #f77e7e; border: 1px solid #5e2a2a; border-radius: 6px; padding: 2px 10px; font-size: 0.78rem; margin: 2px; }
    .badge-blue { display: inline-block; background: #1a1a2e; color: #7eb8f7; border: 1px solid #2e4a6e; border-radius: 6px; padding: 2px 10px; font-size: 0.78rem; margin: 2px; }
    .metric-box { background: #1a1a1a; border: 1px solid #2a2a2a; border-radius: 10px; padding: 16px; text-align: center; }
    .metric-number { color: #7eb8f7; font-size: 1.6rem; font-weight: 700; }
    .metric-label { color: #666; font-size: 0.8rem; margin-top: 4px; }
    .divider { border: none; border-top: 1px solid #222; margin: 24px 0; }
    .hint { color: #444; font-size: 0.82rem; }
    .stButton > button { background: #ffffff; color: #000; border: none; border-radius: 8px; font-weight: 600; padding: 0.6rem 2rem; }
    .stTextInput > div > div > input { background: #1a1a1a; color: #fff; border: 1px solid #333; border-radius: 8px; }
    .stTabs [data-baseweb="tab-list"] { gap: 8px; background: transparent; }
    .stTabs [data-baseweb="tab"] { background: #1a1a1a; border-radius: 8px; color: #666; padding: 8px 20px; border: 1px solid #2a2a2a; }
    .stTabs [aria-selected="true"] { background: #fff !important; color: #000 !important; }
</style>
""", unsafe_allow_html=True)

st.markdown("# 🎯 內容選題生產器")
st.markdown("<p style='color:#666;margin-top:-12px'>基於真實數據的內容切角靈感工具</p>", unsafe_allow_html=True)
st.markdown("<hr class='divider'>", unsafe_allow_html=True)

tab1, tab2 = st.tabs(["📈  熱門話題研究", "👤  KOL 競品分析"])


# ════════════════════════════════════════════════════
# TAB 1 — 熱門話題研究
# ════════════════════════════════════════════════════

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


def build_topic_report(keyword, trends, news):
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


with tab1:
    col_in, col_btn = st.columns([4, 1])
    with col_in:
        keyword = st.text_input("", placeholder="輸入產業關鍵字，例如：咖啡、健身、親子教育", key="kw", label_visibility="collapsed")
    with col_btn:
        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
        run1 = st.button("開始分析 →", key="run1")

    st.markdown("<p class='hint'>🌏 台灣地區｜⏱ 近 12 個月｜資料來源：Google Trends + Google 新聞</p>", unsafe_allow_html=True)

    if run1 and keyword:
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
        st.code(build_topic_report(keyword, trends, news), language=None)

    elif run1 and not keyword:
        st.warning("請先輸入產業關鍵字")


# ════════════════════════════════════════════════════
# TAB 2 — KOL 競品分析
# ════════════════════════════════════════════════════

def extract_channel_id(youtube, raw):
    raw = raw.strip()
    if re.match(r"^UC[\w-]{22}$", raw):
        return raw
    m = re.search(r"/channel/(UC[\w-]{22})", raw)
    if m:
        return m.group(1)
    handle = re.search(r"@([\w.-]+)", raw)
    if handle:
        try:
            r = youtube.channels().list(part="id", forHandle=f"@{handle.group(1)}").execute()
            if r.get("items"):
                return r["items"][0]["id"]
        except Exception:
            pass
    # 用名稱搜尋（消耗 100 單位，最後手段）
    try:
        r = youtube.search().list(q=raw, part="snippet", type="channel", maxResults=1).execute()
        if r.get("items"):
            return r["items"][0]["snippet"]["channelId"]
    except Exception:
        pass
    return None


def fetch_kol(youtube, channel_id):
    """用 RSS + videos.list + channels.list 分析頻道，幾乎不消耗配額"""
    # 1. RSS 拿最新影片（免費）
    rss_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
    feed = feedparser.parse(rss_url)
    if not feed.entries:
        return None

    # 2. channels.list 拿訂閱數（1 單位）
    try:
        ch_resp = youtube.channels().list(part="snippet,statistics", id=channel_id).execute()
        ch_item = ch_resp["items"][0] if ch_resp.get("items") else {}
        subs = int(ch_item.get("statistics", {}).get("subscriberCount", 0))
        ch_name = ch_item.get("snippet", {}).get("title", channel_id)
        total_views = int(ch_item.get("statistics", {}).get("viewCount", 0))
        total_vids = int(ch_item.get("statistics", {}).get("videoCount", 1))
        overall_avg = total_views // total_vids if total_vids else 0
    except Exception:
        subs, ch_name, overall_avg = 0, channel_id, 0

    # 3. videos.list 拿最新 15 支影片數據（1 單位）
    video_ids = [e.yt_videoid for e in feed.entries[:15] if hasattr(e, "yt_videoid")]
    videos = []
    if video_ids:
        try:
            v_resp = youtube.videos().list(part="statistics,snippet", id=",".join(video_ids)).execute()
            one_year_ago = datetime.utcnow() - timedelta(days=365)
            for v in v_resp["items"]:
                pub_str = v["snippet"].get("publishedAt", "")
                try:
                    pub_dt = datetime.strptime(pub_str[:10], "%Y-%m-%d")
                    if pub_dt < one_year_ago:
                        continue
                except Exception:
                    pass
                vw = int(v["statistics"].get("viewCount", 0))
                anomaly = []
                if subs > 0 and vw > subs:
                    anomaly.append(f"觀看是訂閱數 {vw/subs:.1f}x")
                if overall_avg > 0 and vw > overall_avg * 2:
                    anomaly.append(f"觀看是頻道均值 {vw/overall_avg:.1f}x")
                videos.append({
                    "title": v["snippet"].get("title", ""),
                    "views": vw,
                    "published": pub_str[:10],
                    "url": f"https://youtube.com/watch?v={v['id']}",
                    "anomaly": anomaly,
                })
            videos.sort(key=lambda x: x["views"], reverse=True)
        except Exception:
            pass

    # 近期均值（只算抓到的影片）
    recent_avg = sum(v["views"] for v in videos) // len(videos) if videos else 0

    return {
        "name": ch_name,
        "channel_id": channel_id,
        "subscribers": subs,
        "overall_avg": overall_avg,
        "recent_avg": recent_avg,
        "videos": videos,
    }


def build_kol_report(kol_list):
    lines = [f"日期：{datetime.now().strftime('%Y-%m-%d')}", "地區：台灣｜時間範圍：近 12 個月", ""]
    for kol in kol_list:
        lines.append(f"=== KOL：{kol['name']} ===")
        lines.append(f"訂閱數：{kol['subscribers']:,}｜頻道整體均值：{kol['overall_avg']:,}｜近期均值：{kol['recent_avg']:,}")
        anomaly_vids = [v for v in kol["videos"] if v["anomaly"]]
        if anomaly_vids:
            lines.append("爆款影片：")
            for v in anomaly_vids[:3]:
                lines.append(f"  ★ [{v['views']:,}] {v['title']} — {', '.join(v['anomaly'])}")
        lines.append("近期影片 Top 5：")
        for v in kol["videos"][:5]:
            lines.append(f"  [{v['views']:,}] {v['title']}（{v['published']}）")
        lines.append("")
    lines += [
        "---",
        "請根據以上 KOL 競品資料，分析這些頻道的爆款規律，並幫我找出可以參考或差異化的內容切角方向。",
    ]
    return "\n".join(lines)


with tab2:
    st.markdown("<p style='color:#666'>輸入最多 5 個對標 YouTube 頻道，分析近期爆款規律</p>", unsafe_allow_html=True)
    st.markdown("<p class='hint'>支援：頻道連結（@handle 或 /channel/UC...）、頻道名稱</p>", unsafe_allow_html=True)

    kol_inputs = []
    cols = st.columns(2)
    for i in range(5):
        col = cols[i % 2]
        with col:
            val = st.text_input(f"KOL {i+1}", placeholder="https://www.youtube.com/@channelname", key=f"kol_{i}")
            if val.strip():
                kol_inputs.append(val.strip())

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
    run2 = st.button("開始分析 →", key="run2")
    st.markdown("<p class='hint'>🔋 此分析幾乎不消耗 YouTube API 配額</p>", unsafe_allow_html=True)

    if run2 and kol_inputs:
        youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)
        kol_results = []
        progress = st.progress(0, text="正在分析頻道…")

        for i, raw in enumerate(kol_inputs):
            progress.progress((i + 1) / len(kol_inputs), text=f"分析中：{raw[:40]}")
            cid = extract_channel_id(youtube, raw)
            if cid:
                info = fetch_kol(youtube, cid)
                if info:
                    kol_results.append(info)

        progress.empty()

        if not kol_results:
            st.error("找不到任何頻道，請確認輸入的連結或名稱是否正確")
        else:
            st.markdown("<hr class='divider'>", unsafe_allow_html=True)

            c1, c2, c3 = st.columns(3)
            total_anomaly = sum(len([v for v in k["videos"] if v["anomaly"]]) for k in kol_results)
            with c1:
                st.markdown(f"<div class='metric-box'><div class='metric-number'>{len(kol_results)}</div><div class='metric-label'>分析頻道數</div></div>", unsafe_allow_html=True)
            with c2:
                st.markdown(f"<div class='metric-box'><div class='metric-number'>{sum(len(k['videos']) for k in kol_results)}</div><div class='metric-label'>近期影片總數</div></div>", unsafe_allow_html=True)
            with c3:
                st.markdown(f"<div class='metric-box'><div class='metric-number'>{total_anomaly}</div><div class='metric-label'>爆款異常值影片</div></div>", unsafe_allow_html=True)

            st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

            for kol in kol_results:
                st.markdown(f"### 👤 {kol['name']}")
                m1, m2, m3 = st.columns(3)
                with m1:
                    st.markdown(f"<div class='metric-box'><div class='metric-number'>{kol['subscribers']:,}</div><div class='metric-label'>訂閱數</div></div>", unsafe_allow_html=True)
                with m2:
                    st.markdown(f"<div class='metric-box'><div class='metric-number'>{kol['overall_avg']:,}</div><div class='metric-label'>頻道整體均值</div></div>", unsafe_allow_html=True)
                with m3:
                    st.markdown(f"<div class='metric-box'><div class='metric-number'>{kol['recent_avg']:,}</div><div class='metric-label'>近期均值</div></div>", unsafe_allow_html=True)

                st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

                anomaly_vids = [v for v in kol["videos"] if v["anomaly"]]
                if anomaly_vids:
                    st.markdown("**🔥 爆款異常值影片**")
                    for v in anomaly_vids[:3]:
                        badges = "".join([f"<span class='badge-red'>{a}</span>" for a in v["anomaly"]])
                        st.markdown(f"""
                        <div class='card'>
                            <a href='{v['url']}' target='_blank' style='color:#fff;text-decoration:none;font-size:0.92rem'>▶ {v['title']}</a>
                            <div class='hint' style='margin-top:6px'>{v['views']:,} 觀看 · {v['published']}</div>
                            <div style='margin-top:6px'>{badges}</div>
                        </div>
                        """, unsafe_allow_html=True)

                st.markdown("**近期影片（依觀看數排序）**")
                for v in kol["videos"][:8]:
                    is_anomaly = bool(v["anomaly"])
                    color = "#f77e7e" if is_anomaly else "#ccc"
                    st.markdown(f"""
                    <div style='padding:8px 0;border-bottom:1px solid #1e1e1e'>
                        <a href='{v['url']}' target='_blank' style='color:{color};text-decoration:none;font-size:0.88rem'>{v['title']}</a>
                        <span style='color:#555;font-size:0.8rem;margin-left:10px'>{v['views']:,} 觀看 · {v['published']}</span>
                    </div>
                    """, unsafe_allow_html=True)

                st.markdown("<hr class='divider'>", unsafe_allow_html=True)

            st.markdown("### 📋 複製報告，貼給 Claude 分析切角方向")
            st.markdown("<p class='hint'>複製下方內容，貼到 Claude Code 對話框，請 Claude 幫你找出差異化切角</p>", unsafe_allow_html=True)
            st.code(build_kol_report(kol_results), language=None)

    elif run2 and not kol_inputs:
        st.warning("請至少輸入一個 KOL 頻道連結或名稱")
