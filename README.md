# Rural housing RSS feeds

by Ben Winchester, Rural Sociologist. November, 2026.

RSS 2.0 feeds published by Ben Winchester's rural housing research dashboards, one file per
tool. They are plain files in this public repository so that any feed reader, including the
cloud fetcher behind his own Feed Reader, can subscribe to them from anywhere.

| Feed | Address | Built by |
|---|---|---|
| Scaffolding Rural Housing: Dashboard (Projects and Funding channels) | https://raw.githubusercontent.com/ruralben/rural-housing-rss-feeds/main/scaffolding-dashboard.xml | `Scaffolding/build/build_feed.py`, after each scan |
| Rural Narrative Watch (how public voices frame rural places; titles start with a framing score, −2 deficit to +2 asset) | https://raw.githubusercontent.com/ruralben/rural-housing-rss-feeds/main/rural-narrative-watch.xml | `tools/rural_narrative_watch_feed.py`, after each weekly scan (runs in the cloud) |

Each item's date is the day it was added to the dashboard, so new items show as new; an
item's own date (a report's publication, a funding round that opens next spring) is in the
text. The newest 100 items are kept.

The dashboards themselves are private pages; the feeds carry each item's headline, link,
the figure that matters and a one-paragraph note on why it matters to the research.
