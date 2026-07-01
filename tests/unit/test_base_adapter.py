"""适配器基类单元测试"""
import pytest
from adapters.base_adapter import BaseAdapter, AdapterResult


def test_adapter_result_success():
    """测试 AdapterResult 成功状态"""
    result = AdapterResult(
        platform="doubao",
        platform_name="豆包",
        status="success",
        answer="测试答案",
        duration_ms=1000,
        screenshot_path="/tmp/test.png",
        error=None,
    )
    assert result.platform == "doubao"
    assert result.status == "success"
    assert result.answer == "测试答案"
    assert result.is_success is True


def test_adapter_result_failure():
    """测试 AdapterResult 失败状态"""
    result = AdapterResult(
        platform="chatglm",
        platform_name="智谱清言",
        status="failed",
        answer=None,
        duration_ms=120000,
        screenshot_path="/tmp/test.png",
        error="超时",
    )
    assert result.status == "failed"
    assert result.is_success is False
    assert result.error == "超时"


def test_adapter_result_to_dict():
    """测试 AdapterResult 转 dict"""
    result = AdapterResult(
        platform="doubao",
        platform_name="豆包",
        status="success",
        answer="答案",
        duration_ms=500,
        screenshot_path="/tmp/s.png",
        error=None,
    )
    d = result.to_dict()
    assert d["platform"] == "doubao"
    assert d["platform_name"] == "豆包"
    assert d["status"] == "success"
    assert d["answer"] == "答案"
    assert d["duration_ms"] == 500
    assert d["screenshot_path"] == "/tmp/s.png"
    assert d["error"] is None


def test_base_adapter_is_abstract():
    """测试 BaseAdapter 不能直接实例化"""
    with pytest.raises(TypeError):
        BaseAdapter(
            platform_id="test",
            platform_name="测试",
            base_url="https://example.com",
        )
