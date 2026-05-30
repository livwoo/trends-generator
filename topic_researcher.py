"""
內容選題研究工具
用法：python3 topic_researcher.py --industry 咖啡
"""

import argparse
import json
import sys
from datetime import datetime

from googleapiclient.discovery import build
from pytrends.request import TrendReq

YOUTUBE_API_KEY = "AIzaSyCziv8MOOyEMmcb-u4K64B9k_K6lnL0O5E"


def search_youtube_videos(youtube, query, max_results=20):
    """搜尋 YouTube 影片並回傳基本資訊"""
    response = youtube.search().list(
        q=query,
        part="snippet",
        type="video",
        maxResults=max_results,
        order="viewCount",
        regionCode="TW",
        relevanceLanguage="zh-Hant",
    ).execute()

    video_ids = [item["id"]["videoId"] for item in response["items"]]
    return video_ids, response["items"]


def get_video_stats(youtube, video_ids):
    """取得影片詳細數據"""
    response = youtube.videos().list(
        part="statistics,snippet",
        id=",".join(video_ids),
    ).execute()
    return response["items"]


def get_channel_avg_views(youtube, channel_id):
    """計算頻道最近 10 支影片的平均觀看數"""
    try:
        response = youtube.search().list(
            channelId=channel_id,
            part="id",
            type="video",
            maxResults=10,
            order="date",
        ).execute()
        vid_ids = [item["id"]["videoId"] for item in response.get("items", [])]
        if not vid_ids:
            return 0
        stats = youtube.videos().list(part="statistics", id=",".join(vid_ids)).execute()
        views = [
            int(v["statistics"].get("viewCount", 0))
            for v in stats["items"]
        ]
        return sum(views) // len(views) if views else 0
    except Exception:
        return 0


def get_channel_subscribers(youtube, channel_id):
    """取得頻道訂閱數"""
    try:
        response = youtube.channels().list(
            part="statistics",
            id=channel_id,
        ).execute()
        items = response.get("items", [])
        if items:
            return int(items[0]["statistics"].get("subscriberCount", 0))
    except Exception:
        pass
    return 0


def analyze_youtube(industry):
    """分析 YouTube 數據，找出異常值影片"""
    print(f"\n🔍 正在搜尋 YouTube「{industry}」相關影片...", flush=True)
    youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)

    video_ids, search_items = search_youtube_videos(youtube, industry)
    if not video_ids:
        return []

    video_stats = get_video_stats(youtube, video_ids)

    results = []
    for video in video_stats:
        stats = video.get("statistics", {})
        snippet = video.get("snippet", {})
        views = int(stats.get("viewCount", 0))
        channel_id = snippet.get("channelId", "")
        channel_title = snippet.get("channelTitle", "")

        subscribers = get_channel_subscribers(youtube, channel_id)
        channel_avg = get_channel_avg_views(youtube, channel_id)

        anomaly_flags = []
        if subscribers > 0 and views > subscribers:
            ratio = views / subscribers
            anomaly_flags.append(f"觀看數是訂閱數 {ratio:.1f} 倍（爆款切角）")
        if channel_avg > 0 and views > channel_avg * 2:
            ratio = views / channel_avg
            anomaly_flags.append(f"觀看數是頻道均值 {ratio:.1f} 倍（切角異常好）")

        results.append({
            "title": snippet.get("title", ""),
            "channel": channel_title,
            "views": views,
            "subscribers": subscribers,
            "channel_avg": channel_avg,
            "anomaly": anomaly_flags,
            "url": f"https://youtube.com/watch?v={video['id']}",
            "published": snippet.get("publishedAt", "")[:10],
        })

    results.sort(key=lambda x: len(x["anomaly"]), reverse=True)
    return results


def get_google_trends(industry):
    """取得 Google Trends 台灣熱搜關鍵字"""
    print(f"\n📈 正在查詢 Google Trends（台灣）...", flush=True)
    try:
        pytrends = TrendReq(hl="zh-TW", tz=480)
        pytrends.build_payload([industry], cat=0, timeframe="now 7-d", geo="TW")
        related = pytrends.related_queries()

        top_queries = []
        if industry in related and related[industry]["top"] is not None:
            top_df = related[industry]["top"]
            top_queries = top_df["query"].head(10).tolist()

        rising_queries = []
        if industry in related and related[industry]["rising"] is not None:
            rising_df = related[industry]["rising"]
            rising_queries = rising_df["query"].head(5).tolist()

        return {"top": top_queries, "rising": rising_queries}
    except Exception as e:
        return {"top": [], "rising": [], "error": str(e)}


def format_report(industry, youtube_data, trends_data):
    """格式化輸出報告"""
    now = datetime.now().strftime("%Y-%m-%d")
    report = []
    report.append(f"\n{'='*60}")
    report.append(f"📊 內容選題研究報告 ── {industry}")
    report.append(f"📅 {now}")
    report.append(f"{'='*60}")

    report.append("\n## 一、Google Trends 台灣熱搜關鍵字（近 7 天）")
    if trends_data.get("top"):
        report.append("熱門關鍵字：")
        for i, q in enumerate(trends_data["top"], 1):
            report.append(f"  {i}. {q}")
    else:
        report.append("  （無資料）")

    if trends_data.get("rising"):
        report.append("急速上升：")
        for q in trends_data["rising"]:
            report.append(f"  ↑ {q}")

    report.append("\n## 二、YouTube 異常值影片（觀看數遠超訂閱數或頻道均值）")
    anomaly_videos = [v for v in youtube_data if v["anomaly"]]
    if anomaly_videos:
        for v in anomaly_videos[:8]:
            report.append(f"\n▶ {v['title']}")
            report.append(f"   頻道：{v['channel']}｜觀看：{v['views']:,}｜訂閱：{v['subscribers']:,}｜頻道均值：{v['channel_avg']:,}")
            for flag in v["anomaly"]:
                report.append(f"   🔥 {flag}")
            report.append(f"   {v['url']}")
    else:
        report.append("  （未找到明顯異常值影片）")

    report.append("\n## 三、YouTube 高觀看影片 Top 10")
    for i, v in enumerate(youtube_data[:10], 1):
        report.append(f"  {i}. [{v['views']:>8,} 觀看] {v['title']} ── {v['channel']}")

    report.append(f"\n{'='*60}")
    report.append("✅ 資料收集完成。請將此報告交給 Claude 生成 10 組內容切角。")
    report.append(f"{'='*60}\n")

    return "\n".join(report)


def main():
    parser = argparse.ArgumentParser(description="內容選題研究工具")
    parser.add_argument("--industry", required=True, help="輸入產業關鍵字，例如：咖啡")
    args = parser.parse_args()

    industry = args.industry

    youtube_data = analyze_youtube(industry)
    trends_data = get_google_trends(industry)

    report = format_report(industry, youtube_data, trends_data)
    print(report)

    output_file = f"research_{industry}_{datetime.now().strftime('%Y%m%d_%H%M')}.txt"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(report)
    print(f"📁 報告已儲存至：{output_file}")


if __name__ == "__main__":
    main()
