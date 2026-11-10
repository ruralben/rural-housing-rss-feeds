# Cloud copy of Scaffolding/build/build_feed.py, used by the "Scaffolding housing scan (cloud)" routine.
# Same output; only REPO differs. Keep the two in step if the feed format changes.
"""Build feed.xml (RSS 2.0) from the Scaffolding Dashboard's tracker items.

Usage: python build_feed.py <folder or .json file>

A folder is what ArtifactData `list` (collection "tracker", out_dir) saves: one
<id>.json per item under <out_dir>/tracker/. A .json file may instead hold a list
of items (or of {id, data} docs). Writes feed.xml in the Scaffolding project folder
(one level above this script) with the newest LIMIT arrivals from both channels.

Each item's pubDate is the day it was added to the Dashboard (`added`), so a reader
shows new items as new even when the item is a date to watch months ahead; the
item's own date is in the text. Modeled on the Rural Narrative Watch feed builder.
"""
import html
import json
import sys
from datetime import datetime, timezone
from email.utils import format_datetime
from pathlib import Path
from xml.sax.saxutils import escape

DASHBOARD = "https://claude.ai/artifact/A4S439XhtmZWoTeoa5kMnz"
# The feed is published through the public repository ruralben/rural-housing-rss-feeds, cloned at
# 1.Claude/Personal/rural-housing-rss-feeds, so the Feed Reader's cloud fetcher can reach it:
# https://raw.githubusercontent.com/ruralben/rural-housing-rss-feeds/main/scaffolding-dashboard.xml
REPO = Path(__file__).resolve().parent.parent  # cloud copy: this file lives in <repo>/tools/
OUT = REPO / "scaffolding-dashboard.xml"
LIMIT = 100
KIND = {"report": "Report or study", "news": "News coverage", "award": "Award or funding",
        "project": "Project milestone", "policy": "Policy or board action", "new-org": "New institution",
        "people": "People", "data": "Data release", "program": "Program", "finding": "Measured finding",
        "round": "Round opens or closes", "watch": "Date to watch"}
CHANNEL = {"funding": "Funding", "projects": "Projects"}


def load(src):
    src = Path(src)
    if src.is_dir():
        raw = [json.loads(f.read_text(encoding="utf-8")) for f in src.rglob("*.json")]
    else:
        raw = json.loads(src.read_text(encoding="utf-8"))
        raw = raw.get("docs", raw) if isinstance(raw, dict) else raw
    items = []
    for d in raw:
        if isinstance(d, dict) and "data" in d and isinstance(d["data"], dict):
            d = dict(d["data"], id=d.get("id", d["data"].get("id")))
        if isinstance(d, dict) and d.get("title"):
            items.append(d)
    return items


def day(v):
    try:
        dt = datetime.fromisoformat(str(v).replace("Z", "+00:00"))
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(hour=12, tzinfo=timezone.utc)
    return dt


def when(d):
    return day(d.get("added")) or day(d.get("date")) or datetime(2026, 1, 1, tzinfo=timezone.utc)


def arr(v):
    return v if isinstance(v, list) else ([v] if v else [])


def entry(d):
    chan = CHANNEL.get(d.get("channel"), "Projects")
    kind = KIND.get(d.get("kind"), d.get("kind") or "item")
    bits = [b for b in (kind, d.get("source"), ", ".join(arr(d.get("states"))),
                        ("dated " + d["date"]) if d.get("date") else "") if b]
    body = []
    if d.get("figure"):
        body.append("<p><b>%s</b></p>" % html.escape(d["figure"]))
    if d.get("summary"):
        body.append("<p>%s</p>" % html.escape(d["summary"]))
    body.append("<p>%s</p>" % html.escape(" · ".join(bits)))
    if arr(d.get("orgs")):
        body.append("<p>Named: %s</p>" % html.escape(", ".join(arr(d["orgs"]))))
    if d.get("candidate"):
        body.append("<p>Flagged as a possible new case.</p>")
    body.append('<p><a href="%s#dashboard">Open the Scaffolding Dashboard</a></p>' % DASHBOARD)
    title = "[%s] %s" % (chan, d["title"])
    link = d.get("url") or (DASHBOARD + "#dashboard")
    out = ["<item>",
           "<title>%s</title>" % escape(title),
           "<link>%s</link>" % escape(link),
           '<guid isPermaLink="false">scaf-%s</guid>' % escape(str(d.get("id", d["title"]))),
           "<pubDate>%s</pubDate>" % format_datetime(when(d)),
           "<category>%s</category>" % escape(chan),
           "<category>%s</category>" % escape(kind)]
    for s in arr(d.get("states")):
        out.append("<category>%s</category>" % escape(str(s)))
    for a in arr(d.get("authors")):
        out.append("<dc:creator>%s</dc:creator>" % escape(str(a)))
    out.append("<description>%s</description>" % escape("".join(body)))
    out.append("</item>")
    return "\n".join(out)


def main():
    items = sorted(load(sys.argv[1]), key=when, reverse=True)[:LIMIT]
    now = format_datetime(datetime.now(timezone.utc))
    xml = ['<?xml version="1.0" encoding="UTF-8"?>',
           '<rss version="2.0" xmlns:dc="http://purl.org/dc/elements/1.1/">',
           "<channel>",
           "<title>Scaffolding Rural Housing: Dashboard</title>",
           "<link>%s#dashboard</link>" % DASHBOARD,
           "<description>What the institutions around small towns are doing, and where the housing money is going: "
           "new items from the Projects and Funding channels of Ben Winchester's Scaffolding Rural Housing Dashboard.</description>",
           "<language>en-us</language>",
           "<lastBuildDate>%s</lastBuildDate>" % now]
    xml += [entry(d) for d in items]
    xml += ["</channel>", "</rss>", ""]
    OUT.write_text("\n".join(xml), encoding="utf-8")
    print("wrote %d items to %s" % (len(items), OUT))
    if "--no-push" not in sys.argv:
        push(len(items))


def push(n):
    """Commit the feed and push it to GitHub; a run that changed nothing makes no commit."""
    import subprocess
    git = ["git", "-C", str(REPO)]
    subprocess.run(git + ["add", OUT.name], check=True)
    changed = subprocess.run(git + ["diff", "--cached", "--quiet"]).returncode == 1
    if not changed:
        print("feed unchanged; nothing to push")
        return
    subprocess.run(git + ["commit", "-q", "-m", "Scaffolding Dashboard feed: %d items, %s" % (
        n, datetime.now().strftime("%Y-%m-%d %H:%M"))], check=True)
    subprocess.run(git + ["push", "-q", "origin", "HEAD:main"], check=True)
    print("pushed to github.com/ruralben/rural-housing-rss-feeds")


if __name__ == "__main__":
    main()
