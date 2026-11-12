"""Offline tests for crewai_asin (httpx.MockTransport)."""

from __future__ import annotations

import json
from collections.abc import Callable

import httpx
import pytest

import crewai_asin as pkg
from crewai_asin import _client

API_KEY = "test-asin-key-placeholder"  # pragma: allowlist secret
BASE = "https://www.asin.dev/api/v1"
CASES = [
    {
        "cls": "AsinAmazonSearchTool",
        "config": {"marketplace": "de"},
        "sample": {"query": "kindle"},
        "method": "GET",
        "path": "/search",
        "params": {"query": "kindle", "marketplace": "de"},
        "body": None,
        "response": {"ok": True},
        "result": {"ok": True},
    },
    {
        "cls": "AsinPriceHistoryTool",
        "config": {"days": 30},
        "sample": {"asin": "B09DFCB66S"},
        "method": "GET",
        "path": "/history",
        "params": {"asin": "B09DFCB66S", "marketplace": "com", "days": "30"},
        "body": None,
        "response": {"ok": True},
        "result": {"ok": True},
    },
    {
        "cls": "AsinOffersTool",
        "config": {"live": True},
        "sample": {"asin": "B09DFCB66S"},
        "method": "POST",
        "path": "/offers",
        "params": None,
        "body": {"asin": "B09DFCB66S", "marketplace": "com"},
        "response": {"ok": True},
        "result": {"ok": True},
    },
]

Handler = Callable[[httpx.Request], httpx.Response]


@pytest.fixture
def mock_http(monkeypatch: pytest.MonkeyPatch) -> Callable[[Handler], list[httpx.Request]]:
    def install(handler: Handler) -> list[httpx.Request]:
        seen: list[httpx.Request] = []

        def record(request: httpx.Request) -> httpx.Response:
            seen.append(request)
            return handler(request)

        transport = httpx.MockTransport(record)
        real_client, real_async = httpx.Client, httpx.AsyncClient
        monkeypatch.setattr(_client.httpx, "Client", lambda **kw: real_client(transport=transport, **kw))
        monkeypatch.setattr(_client.httpx, "AsyncClient", lambda **kw: real_async(transport=transport, **kw))
        return seen

    return install


def _params(request: httpx.Request) -> dict[str, str]:
    return dict(request.url.params)


def _body(request: httpx.Request) -> object:
    return json.loads(request.content) if request.content else None


@pytest.mark.parametrize("case", CASES, ids=[c["cls"] for c in CASES])
def test_request_and_result(mock_http, case) -> None:
    seen = mock_http(lambda request: httpx.Response(200, json=case["response"]))
    tool = getattr(pkg, case["cls"])(api_key=API_KEY, **case["config"])

    result = tool.run(**case["sample"])

    request = seen[0]
    assert request.method == case["method"]
    assert request.url.copy_with(query=None) == httpx.URL(BASE + case["path"])
    assert _params(request) == (case["params"] or {})
    assert _body(request) == case["body"]
    expected = case["result"]
    assert result == (expected if isinstance(expected, str) else json.dumps(expected, ensure_ascii=False))


@pytest.mark.parametrize(
    ("status", "body", "message"),
    [
        (401, {"error": f"Invalid key {API_KEY}"}, "Asin rejected the API key (HTTP 401): Invalid key ***"),
        (402, {"error": "No credits"}, "Asin account is out of credits (HTTP 402): No credits"),
    ],
)
def test_errors_come_back_as_text(mock_http, status, body, message) -> None:
    mock_http(lambda request: httpx.Response(status, json=body))
    assert pkg.AsinAmazonSearchTool(api_key=API_KEY, **{"marketplace": "de"}).run(**{"query": "kindle"}) == message


def test_missing_key_sends_no_request(mock_http, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ASIN_API_KEY", raising=False)
    seen = mock_http(lambda request: httpx.Response(200, json={}))
    assert "ASIN_API_KEY" in pkg.AsinAmazonSearchTool(**{"marketplace": "de"}).run(**{"query": "kindle"})
    assert seen == []


def test_declares_its_env_var() -> None:
    for name in pkg.__all__:
        tool_cls = getattr(pkg, name)
        if name.endswith("Tool"):
            assert [env.name for env in tool_cls().env_vars] == ["ASIN_API_KEY"]
