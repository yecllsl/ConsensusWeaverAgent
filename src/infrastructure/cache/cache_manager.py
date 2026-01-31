import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, Optional, cast

from src.infrastructure.logging.logger import get_logger


@dataclass
class CacheEntry:
    key: str
    value: Any
    created_at: datetime
    expires_at: Optional[datetime] = None
    hit_count: int = 0


@dataclass
class CacheConfig:
    enabled: bool = True
    max_size: int = 1000
    default_ttl: int = 3600


class MemoryCache:
    def __init__(self, max_size: int = 1000) -> None:
        self.cache: Dict[str, CacheEntry] = {}
        self.max_size = max_size
        self.hit_count = 0
        self.miss_count = 0
        self.logger = get_logger()

    def get(self, key: str) -> Optional[Any]:
        if key not in self.cache:
            self.miss_count += 1
            return None

        entry = self.cache[key]

        if self._is_expired(entry):
            del self.cache[key]
            self.miss_count += 1
            return None

        entry.hit_count += 1
        self.hit_count += 1
        return entry.value

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        if isinstance(value, (dict, list)):
            value = json.dumps(value)

        entry = CacheEntry(
            key=key,
            value=value,
            created_at=datetime.now(),
            expires_at=datetime.now() + timedelta(seconds=ttl) if ttl else None,
        )

        self.cache[key] = entry
        self._enforce_size_limit()

    def delete(self, key: str) -> bool:
        if key in self.cache:
            del self.cache[key]
            return True
        return False

    def clear(self) -> None:
        self.cache.clear()
        self.hit_count = 0
        self.miss_count = 0

    def get_statistics(self) -> Dict[str, Any]:
        total_requests = self.hit_count + self.miss_count
        hit_rate = self.hit_count / total_requests * 100 if total_requests > 0 else 0

        return {
            "total_entries": len(self.cache),
            "hit_count": self.hit_count,
            "miss_count": self.miss_count,
            "hit_rate": hit_rate,
            "max_size": self.max_size,
        }

    def invalidate_pattern(self, pattern: str) -> int:
        keys_to_delete = [k for k in self.cache.keys() if pattern in k]
        for key in keys_to_delete:
            del self.cache[key]
        return len(keys_to_delete)

    def _is_expired(self, entry: CacheEntry) -> bool:
        if entry.expires_at is None:
            return False
        return datetime.now() > entry.expires_at

    def _enforce_size_limit(self) -> None:
        if len(self.cache) <= self.max_size:
            return

        sorted_entries = sorted(self.cache.items(), key=lambda x: x[1].hit_count)

        entries_to_remove = len(self.cache) - self.max_size
        for i in range(entries_to_remove):
            del self.cache[sorted_entries[i][0]]


class CacheManager:
    def __init__(self, config: CacheConfig) -> None:
        self.config = config
        self.memory_cache = MemoryCache(config.max_size) if config.enabled else None
        self.logger = get_logger()

    def get(self, key: str) -> Optional[Any]:
        if not self.config.enabled or not self.memory_cache:
            return None
        return self.memory_cache.get(key)

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        if not self.config.enabled or not self.memory_cache:
            return
        if ttl is None:
            ttl = self.config.default_ttl
        self.memory_cache.set(key, value, ttl)

    def delete(self, key: str) -> bool:
        if not self.config.enabled or not self.memory_cache:
            return False
        return self.memory_cache.delete(key)

    def clear(self) -> None:
        if self.memory_cache:
            self.memory_cache.clear()

    def get_statistics(self) -> Dict[str, Any]:
        if not self.memory_cache:
            return {
                "total_entries": 0,
                "hit_count": 0,
                "miss_count": 0,
                "hit_rate": 0.0,
                "max_size": self.config.max_size,
                "enabled": self.config.enabled,
            }
        stats = self.memory_cache.get_statistics()
        stats["enabled"] = self.config.enabled
        return stats

    def invalidate_pattern(self, pattern: str) -> int:
        if not self.config.enabled or not self.memory_cache:
            return 0
        return self.memory_cache.invalidate_pattern(pattern)


class LLMCache:
    def __init__(self, cache_manager: CacheManager) -> None:
        self.cache_manager = cache_manager
        self.logger = get_logger()
        self._prompt_keys: Dict[tuple[str, str], str] = {}

    def _generate_key(self, prompt: str, model: str = "default") -> str:
        key_data = f"llm:{model}:{prompt}"
        hash_value = hashlib.md5(key_data.encode()).hexdigest()
        key = f"llm:{model}:{hash_value}"
        self._prompt_keys[(prompt, model)] = key
        return key

    def get_response(self, prompt: str, model: str = "default") -> Optional[str]:
        key = self._generate_key(prompt, model)
        cached = self.cache_manager.get(key)
        if cached:
            self.logger.info(f"LLM缓存命中: {prompt[:50]}...")
            if isinstance(cached, str):
                return cached
        return None

    def set_response(
        self,
        prompt: str,
        response: str,
        model: str = "default",
        ttl: Optional[int] = None,
    ) -> None:
        key = self._generate_key(prompt, model)
        self.cache_manager.set(key, response, ttl)

    def invalidate_model(self, model: str = "default") -> int:
        keys_to_delete = []
        for (prompt, mod), key in list(self._prompt_keys.items()):
            if mod == model:
                keys_to_delete.append(key)
                del self._prompt_keys[(prompt, mod)]

        count = 0
        for key in keys_to_delete:
            if self.cache_manager.delete(key):
                count += 1
        return count


class ToolCache:
    def __init__(self, cache_manager: CacheManager) -> None:
        self.cache_manager = cache_manager
        self.logger = get_logger()
        self._tool_keys: Dict[tuple[str, str], str] = {}

    def _generate_key(self, tool_name: str, question: str) -> str:
        key_data = f"tool:{tool_name}:{question}"
        hash_value = hashlib.md5(key_data.encode()).hexdigest()
        key = f"tool:{tool_name}:{hash_value}"
        self._tool_keys[(tool_name, question)] = key
        return key

    def get_result(self, tool_name: str, question: str) -> Optional[Dict[str, Any]]:
        key = self._generate_key(tool_name, question)
        cached = self.cache_manager.get(key)
        if cached:
            self.logger.info(f"工具缓存命中: {tool_name} - {question[:50]}...")
            if isinstance(cached, str):
                return cast(Dict[str, Any], json.loads(cached))
            if isinstance(cached, dict):
                return cast(Dict[str, Any], cached)
        return None

    def set_result(
        self,
        tool_name: str,
        question: str,
        result: Dict[str, Any],
        ttl: Optional[int] = None,
    ) -> None:
        key = self._generate_key(tool_name, question)
        self.cache_manager.set(key, result, ttl)

    def invalidate_tool(self, tool_name: str) -> int:
        keys_to_delete = []
        for (tool, question), key in list(self._tool_keys.items()):
            if tool == tool_name:
                keys_to_delete.append(key)
                del self._tool_keys[(tool, question)]

        count = 0
        for key in keys_to_delete:
            if self.cache_manager.delete(key):
                count += 1
        return count
