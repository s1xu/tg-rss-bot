import feedparser


def fetch_rss_updates(url):
    feed = feedparser.parse(url)
    updates = []
    theme = feed.feed.title
    for entry in feed.entries:
        updates.append({
            'id': entry.link if 'link' in entry else entry.id,
            'title': entry.title,
            'link': entry.link,
            'theme': theme
        })
    # 倒序更新列表
    updates.reverse()
    return updates
