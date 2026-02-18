"""Simple in-memory cooldown manager to avoid hammering providers after 429s.

Stores cooldown timestamps per (provider, model, api_key) key and exposes helpers
to check and set cooldowns. This is intentionally lightweight (process-local).
"""
from typing import Optional, Tuple
import threading
import time


class ProviderCooldownManager:
    def __init__(self):
        self._lock = threading.Lock()
        # key -> reset_timestamp (epoch seconds)
        self._cooldowns = {}

    def _make_key(self, provider: str, model: str, api_key: Optional[str]) -> str:
        key = f"{provider}::{model}::" + (api_key or "__no_key__")
        return key

    def is_on_cooldown(self, provider: str, model: str, api_key: Optional[str]) -> Tuple[bool, int]:
        """Return (on_cooldown, seconds_remaining)."""
        key = self._make_key(provider, model, api_key)
        with self._lock:
            reset = self._cooldowns.get(key)
            if not reset:
                return False, 0
            now = int(time.time())
            if reset <= now:
                # expired
                del self._cooldowns[key]
                return False, 0
            return True, int(reset - now)

    def set_cooldown(self, provider: str, model: str, api_key: Optional[str], seconds: int):
        key = self._make_key(provider, model, api_key)
        reset = int(time.time()) + max(1, int(seconds))
        with self._lock:
            self._cooldowns[key] = reset


# Singleton instance used by the app
cooldown_manager = ProviderCooldownManager()
