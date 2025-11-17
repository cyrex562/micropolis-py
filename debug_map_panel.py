import os

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"
import pygame

pygame.init()
from micropolis.app_config import AppConfig
from micropolis.context import AppContext
from micropolis.ui.event_bus import EventBus
from micropolis.ui.panels.map_panel import MapPanel

cfg = AppConfig()
ctx = AppContext(config=cfg)
eb = EventBus()
panel = MapPanel(rect=pygame.Rect(600, 100, 180, 180), context=ctx, event_bus=eb)
panel.on_mount(ctx)
# Access minimap rect
try:
    mm_rect = panel._view._minimap.rect
    print("minimap rect type:", type(mm_rect))
    try:
        print("minimap as_tuple:", mm_rect.as_tuple())
    except Exception:
        print("minimap tuple:", tuple(mm_rect))
except Exception as e:
    print("error accessing minimap rect", e)
# simulate event
from pygame.event import Event

evt = Event(pygame.MOUSEBUTTONDOWN, {"pos": (650, 150), "button": 1})
handled = panel.handle_panel_event(evt)
print("handled", handled)
# Check if EventBus got published
print(
    "subscriber count for map.location.selected:",
    eb.subscriber_count("map.location.selected"),
)
