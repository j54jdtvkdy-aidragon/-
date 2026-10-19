from .reference import ArxivCollector, WikipediaCollector
from .social import HatenaCollector, RedditCollector
from .video import YouTubeCollector
from .web import NewsCollector, WebCollector

COLLECTORS = {
    c.name: c
    for c in (
        WebCollector(), NewsCollector(), RedditCollector(), HatenaCollector(),
        ArxivCollector(), WikipediaCollector(), YouTubeCollector(),
    )
}
DEFAULT_SOURCES = list(COLLECTORS)
