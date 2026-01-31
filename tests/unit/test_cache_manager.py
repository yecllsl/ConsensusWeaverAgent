import time

import pytest

from src.infrastructure.cache.cache_manager import (
    CacheConfig,
    CacheManager,
    LLMCache,
    MemoryCache,
    ToolCache,
)


@pytest.fixture
def cache_config():
    return CacheConfig(enabled=True, max_size=100, default_ttl=3600)


@pytest.fixture
def cache_manager(cache_config):
    return CacheManager(cache_config)


@pytest.fixture
def memory_cache():
    return MemoryCache(max_size=100)


class TestMemoryCache:
    def test_set_and_get(self, memory_cache):
        memory_cache.set("key1", "value1")
        value = memory_cache.get("key1")

        assert value == "value1"

    def test_cache_miss(self, memory_cache):
        value = memory_cache.get("nonexistent_key")
        assert value is None

    def test_cache_expiration(self, memory_cache):
        memory_cache.set("key1", "value1", ttl=1)
        time.sleep(2)

        value = memory_cache.get("key1")
        assert value is None

    def test_cache_size_limit(self, memory_cache):
        memory_cache.max_size = 10
        for i in range(20):
            memory_cache.set(f"key{i}", f"value{i}")

        stats = memory_cache.get_statistics()
        assert stats["total_entries"] <= 10

    def test_clear_cache(self, memory_cache):
        memory_cache.set("key1", "value1")
        memory_cache.clear()

        stats = memory_cache.get_statistics()
        assert stats["total_entries"] == 0

    def test_cache_statistics(self, memory_cache):
        memory_cache.set("key1", "value1")
        memory_cache.get("key1")
        memory_cache.get("key2")

        stats = memory_cache.get_statistics()
        assert stats["hit_count"] == 1
        assert stats["miss_count"] == 1
        assert stats["hit_rate"] == 50.0

    def test_invalidate_pattern(self, memory_cache):
        memory_cache.set("test:1", "value1")
        memory_cache.set("test:2", "value2")
        memory_cache.set("other:1", "value3")

        count = memory_cache.invalidate_pattern("test:")

        assert count == 2
        assert memory_cache.get("test:1") is None
        assert memory_cache.get("test:2") is None
        assert memory_cache.get("other:1") == "value3"

    def test_delete(self, memory_cache):
        memory_cache.set("key1", "value1")
        result = memory_cache.delete("key1")

        assert result is True
        assert memory_cache.get("key1") is None

    def test_delete_nonexistent(self, memory_cache):
        result = memory_cache.delete("nonexistent")
        assert result is False


class TestCacheManager:
    def test_initialization(self, cache_manager, cache_config):
        assert cache_manager.config == cache_config

    def test_set_and_get(self, cache_manager):
        cache_manager.set("key1", "value1")
        value = cache_manager.get("key1")

        assert value == "value1"

    def test_cache_miss(self, cache_manager):
        value = cache_manager.get("nonexistent_key")
        assert value is None

    def test_cache_disabled(self):
        config = CacheConfig(enabled=False)
        cache_manager = CacheManager(config)

        cache_manager.set("key1", "value1")
        value = cache_manager.get("key1")

        assert value is None

    def test_delete(self, cache_manager):
        cache_manager.set("key1", "value1")
        result = cache_manager.delete("key1")

        assert result is True
        assert cache_manager.get("key1") is None

    def test_clear(self, cache_manager):
        cache_manager.set("key1", "value1")
        cache_manager.clear()

        stats = cache_manager.get_statistics()
        assert stats["total_entries"] == 0

    def test_statistics(self, cache_manager):
        cache_manager.set("key1", "value1")
        cache_manager.get("key1")
        cache_manager.get("key2")

        stats = cache_manager.get_statistics()
        assert stats["hit_count"] == 1
        assert stats["miss_count"] == 1
        assert stats["hit_rate"] == 50.0

    def test_invalidate_pattern(self, cache_manager):
        cache_manager.set("test:1", "value1")
        cache_manager.set("test:2", "value2")
        cache_manager.set("other:1", "value3")

        count = cache_manager.invalidate_pattern("test:")

        assert count == 2
        assert cache_manager.get("test:1") is None
        assert cache_manager.get("test:2") is None
        assert cache_manager.get("other:1") == "value3"


class TestLLMCache:
    def test_get_and_set_response(self, cache_manager):
        llm_cache = LLMCache(cache_manager)

        llm_cache.set_response("test prompt", "test response")
        result = llm_cache.get_response("test prompt")

        assert result == "test response"

    def test_get_nonexistent(self, cache_manager):
        llm_cache = LLMCache(cache_manager)

        result = llm_cache.get_response("nonexistent prompt")

        assert result is None

    def test_different_models(self, cache_manager):
        llm_cache = LLMCache(cache_manager)

        llm_cache.set_response("test prompt", "response1", model="model1")
        llm_cache.set_response("test prompt", "response2", model="model2")

        result1 = llm_cache.get_response("test prompt", model="model1")
        result2 = llm_cache.get_response("test prompt", model="model2")

        assert result1 == "response1"
        assert result2 == "response2"

    def test_invalidate_model(self, cache_manager):
        llm_cache = LLMCache(cache_manager)

        llm_cache.set_response("prompt1", "response1", model="model1")
        llm_cache.set_response("prompt2", "response2", model="model1")
        llm_cache.set_response("prompt3", "response3", model="model2")

        count = llm_cache.invalidate_model("model1")

        assert count >= 0
        assert llm_cache.get_response("prompt1", model="model1") is None
        assert llm_cache.get_response("prompt2", model="model1") is None
        assert llm_cache.get_response("prompt3", model="model2") == "response3"


class TestToolCache:
    def test_get_and_set_result(self, cache_manager):
        tool_cache = ToolCache(cache_manager)

        result_data = {"answer": "test answer", "confidence": 0.9}
        tool_cache.set_result("search", "test question", result_data)
        result = tool_cache.get_result("search", "test question")

        assert result == result_data

    def test_get_nonexistent(self, cache_manager):
        tool_cache = ToolCache(cache_manager)

        result = tool_cache.get_result("search", "nonexistent question")

        assert result is None

    def test_different_tools(self, cache_manager):
        tool_cache = ToolCache(cache_manager)

        result1 = {"answer": "answer1"}
        result2 = {"answer": "answer2"}

        tool_cache.set_result("tool1", "question", result1)
        tool_cache.set_result("tool2", "question", result2)

        retrieved1 = tool_cache.get_result("tool1", "question")
        retrieved2 = tool_cache.get_result("tool2", "question")

        assert retrieved1 == result1
        assert retrieved2 == result2

    def test_invalidate_tool(self, cache_manager):
        tool_cache = ToolCache(cache_manager)

        result1 = {"answer": "answer1"}
        result2 = {"answer": "answer2"}
        result3 = {"answer": "answer3"}

        tool_cache.set_result("tool1", "question1", result1)
        tool_cache.set_result("tool1", "question2", result2)
        tool_cache.set_result("tool2", "question3", result3)

        count = tool_cache.invalidate_tool("tool1")

        assert count >= 0
        assert tool_cache.get_result("tool1", "question1") is None
        assert tool_cache.get_result("tool1", "question2") is None
        assert tool_cache.get_result("tool2", "question3") == result3


class TestCacheConfig:
    def test_defaults(self):
        config = CacheConfig()

        assert config.enabled is True
        assert config.max_size == 1000
        assert config.default_ttl == 3600

    def test_custom_values(self):
        config = CacheConfig(enabled=False, max_size=500, default_ttl=7200)

        assert config.enabled is False
        assert config.max_size == 500
        assert config.default_ttl == 7200
