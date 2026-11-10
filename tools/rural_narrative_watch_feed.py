"""Build rural-narrative-watch.xml (RSS 2.0) from Rural Narrative Watch feed items.

Usage: python tools/rural_narrative_watch_feed.py <folder or .json file> [--no-push]

The input is the dashboard's `items` collection: either a folder as ArtifactData
`list` (collection "items", out_dir) saves it, one <id>.json per item, or a .json
file holding a list of items (or of {id, data} docs). Writes
rural-narrative-watch.xml at the root of this repository with the newest LIMIT
arrivals, then commits and pushes it if it changed (unless --no-push).

Each item's pubDate is when it arrived in the dashboard (added_at), so a reader
shows new items as new; the article's own date is in the text. Runs the same on
Ben's PC and in the weekly cloud scan.
"""
import html
import json
import subprocess
import sys
from datetime import datetime, timezone
from email.utils import format_datetime
from pathlib import Path
from xml.sax.saxutils import escape

DASHBOARD = "https://claude.ai/artifact/Kac6y7h9dF6Pk1NpF12c4n"
REPO = Path(__file__).resolve().parent.parent
OUT = REPO / "rural-narrative-watch.xml"
FEED_URL = "https://raw.githubusercontent.com/ruralben/rural-housing-rss-feeds/main/rural-narrative-watch.xml"
LIMIT = 100
VOICE = {"federal": "Federal", "state": "State", "local": "Local", "media": "News media",
         "advocacy": "Advocacy", "researcher": "Researcher", "film": "Film", "tv": "TV", "book": "Book"}


def load(src):
    src = Path(src)
    if src.is_dir():
        raw = [json.loads(f.read_text(encoding="utf-8")) for f in src.rglob("*.json")]
    else:
        raw = json.loads(src.read_text(encoding="utf-8"))
        raw = raw.get("docs", raw) if isinstance(raw, dict) else raw
    items = []
    for d in raw:
        d = d.get("data", d)  # tolerate {id, data, version} wrappers
        if d.get("title"):
            items.append(d)
    return items


def when(d):
    for key in ("added_at", "date"):
        v = d.get(key) or ""
        try:
            dt = datetime.fromisoformat(v.replace("Z", "+00:00"))
            return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    return datetime(2026, 1, 1, tzinfo=timezone.utc)


def score(n):
    return ("+%d" % n) if isinstance(n, int) and n > 0 else str(n)


def entry(d):
    framing = d.get("framing")
    bits = [b for b in (d.get("outlet"), VOICE.get(d.get("tier"), d.get("tier")), d.get("state"),
                        "published " + d["date"] if d.get("date") else "") if b]
    body = ["<p>%s</p>" % html.escape(d.get("summary", ""))]
    if d.get("quote"):
        body.append("<blockquote>“%s”</blockquote>" % html.escape(d["quote"]))
    body.append("<p><b>Framing %s</b> &middot; %s</p>" % (html.escape(score(framing)), html.escape(" · ".join(bits))))
    if d.get("tags"):
        body.append("<p>Tags: %s</p>" % html.escape(", ".join(d["tags"])))
    body.append('<p><a href="%s">Open Rural Narrative Watch</a></p>' % DASHBOARD)
    title = "[%s] %s" % (score(framing), d["title"])
    link = d.get("url") or DASHBOARD
    out = ["<item>",
           "<title>%s</title>" % escape(title),
           "<link>%s</link>" % escape(link),
           '<guid isPermaLink="false">rnw-%s</guid>' % escape(d.get("id", d["title"])),
           "<pubDate>%s</pubDate>" % format_datetime(when(d))]
    if d.get("speaker"):
        out.append("<dc:creator>%s</dc:creator>" % escape(d["speaker"]))
    for t in d.get("tags", []):
        out.append("<category>%s</category>" % escape(t))
    out.append("<description>%s</description>" % escape("".join(body)))
    out.append("</item>")
    return "\n".join(out)


def main():
    items = sorted(load([a for a in sys.argv[1:] if not a.startswith("--")][0]), key=when, reverse=True)[:LIMIT]
    now = format_datetime(datetime.now(timezone.utc))
    xml = ['<?xml version="1.0" encoding="UTF-8"?>',
           '<rss version="2.0" xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:atom="http://www.w3.org/2005/Atom">',
           "<channel>",
           "<title>Rural Narrative Watch</title>",
           "<link>%s</link>" % DASHBOARD,
           '<atom:link href="%s" rel="self" type="application/rss+xml"/>' % FEED_URL,
           "<description>How public voices frame rural places: new items from Ben Winchester's Rural Narrative Watch.</description>",
           "<language>en-us</language>",
           "<lastBuildDate>%s</lastBuildDate>" % now]
    xml += [entry(d) for d in items]
    xml += ["</channel>", "</rss>", ""]
    OUT.write_text("\n".join(xml), encoding="utf-8")
    print("wrote %d items to %s" % (len(items), OUT))
    publish(len(items))


def git(*args):
    return subprocess.run(["git", "-C", str(REPO), *args], capture_output=True, text=True)


def publish(n):
    if "--no-push" in sys.argv:
        print("--no-push: not committed")
        return
    git("pull", "--rebase", "-q", "origin", "main")
    git("add", OUT.name)
    if git("diff", "--cached", "--quiet").returncode == 0:
        print("feed unchanged on GitHub")
        return
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    r = git("commit", "-q", "-m", "Rural Narrative Watch feed: %d items, %s" % (n, stamp))
    if r.returncode:
        sys.exit("git commit failed: " + r.stderr)
    r = git("push", "-q", "origin", "HEAD:main")
    if r.returncode:
        sys.exit("git push failed: " + r.stderr)
    print("published to", FEED_URL)

if __name__ == "__main__":
    main()
