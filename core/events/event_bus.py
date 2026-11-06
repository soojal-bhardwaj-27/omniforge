import asyncio
import json
import logging
from typing import Callable, Dict, List, Any
from dataclasses import dataclass, asdict
from datetime import datetime

logger = logging.getLogger("omniforge.events")


@dataclass
class MissionEvent:
    mission_id: str
    agent: str
    event_type: str
    message: str
    task_id: str = ""
    payload: Dict[str, Any] = None
    timestamp: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.utcnow().isoformat()
        if self.payload is None:
            self.payload = {}

    def to_dict(self):
        return asdict(self)

    def to_json(self):
        return json.dumps(self.to_dict())


class EventBus:
    """In-memory asynchronous event bus supporting subscribers and WebSocket broadcasting
    with bounded queues to prevent memory exhaustion under high load.
    """

    def __init__(self, max_queue_size: int = 500):
        self._max_queue_size = max_queue_size
        self._subscribers: List[asyncio.Queue] = []
        self._mission_subscribers: Dict[str, List[asyncio.Queue]] = {}
        self._callbacks: List[Callable[[MissionEvent], Any]] = []

    def register_callback(self, callback: Callable[[MissionEvent], Any]):
        self._callbacks.append(callback)

    def subscribe(self, mission_id: str = "") -> asyncio.Queue:
        q = asyncio.Queue(maxsize=self._max_queue_size)
        if mission_id:
            if mission_id not in self._mission_subscribers:
                self._mission_subscribers[mission_id] = []
            self._mission_subscribers[mission_id].append(q)
        else:
            self._subscribers.append(q)
        return q

    def unsubscribe(self, q: asyncio.Queue, mission_id: str = ""):
        if mission_id and mission_id in self._mission_subscribers:
            if q in self._mission_subscribers[mission_id]:
                self._mission_subscribers[mission_id].remove(q)
        elif q in self._subscribers:
            self._subscribers.remove(q)

    def _safe_put(self, q: asyncio.Queue, event: MissionEvent):
        """Pushes to queue, safely evicting oldest item if full to enforce bound."""
        if q.full():
            try:
                q.get_nowait()
            except Exception:
                pass
        try:
            q.put_nowait(event)
        except Exception as e:
            logger.debug(f"Event queue push error: {e}")

    async def publish(self, event: MissionEvent):
        # Notify global subscribers
        for q in list(self._subscribers):
            self._safe_put(q, event)

        # Notify mission-specific subscribers
        if event.mission_id in self._mission_subscribers:
            for q in list(self._mission_subscribers[event.mission_id]):
                self._safe_put(q, event)

        # Trigger callbacks
        for cb in self._callbacks:
            try:
                if asyncio.iscoroutinefunction(cb):
                    await cb(event)
                else:
                    cb(event)
            except Exception as e:
                logger.error(f"Error executing event callback: {e}")


# Singleton instance
global_event_bus = EventBus()
