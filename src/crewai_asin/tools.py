"""Asin tools for CrewAI agents."""

from __future__ import annotations

import json
from typing import Any

from crewai.tools import BaseTool, EnvVar
from pydantic import BaseModel, Field

from crewai_asin import _client


class _AsinTool(BaseTool):
    """Shared settings and request handling for the Asin tools. Errors come back as text."""

    api_key: str | None = Field(default=None, description="Asin API key. Defaults to ASIN_API_KEY.")
    base_url: str = _client.DEFAULT_BASE_URL
    timeout: float = _client.DEFAULT_TIMEOUT
    env_vars: list[EnvVar] = Field(
        default_factory=lambda: [EnvVar(name="ASIN_API_KEY", description="API key for Asin", required=True)]
    )

    def _output(self, data: Any) -> Any:
        return data

    def _send(self, method: str, path: str, params: dict[str, Any] | None, body: dict[str, Any] | None) -> Any:
        api_key = _client.resolve_api_key(self.api_key)
        return _client.request(
            method,
            path,
            params=_client.clean(params) if params else None,
            json=body,
            api_key=api_key,
            base_url=self.base_url,
            timeout=self.timeout,
        )

    @staticmethod
    def _text(data: Any) -> str:
        return data if isinstance(data, str) else json.dumps(data, ensure_ascii=False)


class AsinAmazonSearchToolSchema(BaseModel):
    """Input for AsinAmazonSearchTool."""

    query: str = Field(default=..., description="What to search for on Amazon.")


class AsinAmazonSearchTool(_AsinTool):
    """Search an Amazon store through Asin."""

    name: str = "Search Amazon with Asin"
    description: str = "Search an Amazon store with Asin and get up to 60 products with their ASIN, title, price, rating and review count. Input is the search keywords."
    args_schema: type[BaseModel] = AsinAmazonSearchToolSchema
    marketplace: str = "com"
    """Amazon store: com, co.uk, de, fr, it, es, ca, co.jp, com.br, com.mx or in."""

    def _request(self, query: str) -> tuple[str, str, dict[str, Any] | None, dict[str, Any] | None]:
        return "GET", "/search", {"query": _client.required(query, "query"), "marketplace": self.marketplace}, None

    def _run(self, query: str, **kwargs: Any) -> str:
        try:
            return self._text(self._output(self._send(*self._request(query))))
        except _client.AsinError as exc:
            return str(exc)


class AsinPriceHistoryToolSchema(BaseModel):
    """Input for AsinPriceHistoryTool."""

    asin: str = Field(default=..., description="The 10-character ASIN, such as B09DFCB66S.")


class AsinPriceHistoryTool(_AsinTool):
    """Read the price history of an Amazon product through Asin."""

    name: str = "Get an Amazon price history with Asin"
    description: str = "Get the price history of an Amazon product with Asin: every price read over the period, with the lowest, highest and average. Use it to tell whether the current price is a good one. Input is the ASIN."
    args_schema: type[BaseModel] = AsinPriceHistoryToolSchema
    marketplace: str = "com"
    """Amazon store, such as com, co.uk, de or fr."""
    days: int = Field(default=90, ge=1)
    """History period in days."""

    def _request(self, asin: str) -> tuple[str, str, dict[str, Any] | None, dict[str, Any] | None]:
        return (
            "GET",
            "/history",
            {"asin": _client.required(asin, "asin"), "marketplace": self.marketplace, "days": self.days},
            None,
        )

    def _run(self, asin: str, **kwargs: Any) -> str:
        try:
            return self._text(self._output(self._send(*self._request(asin))))
        except _client.AsinError as exc:
            return str(exc)


class AsinOffersToolSchema(BaseModel):
    """Input for AsinOffersTool."""

    asin: str = Field(default=..., description="The 10-character ASIN, such as B09DFCB66S.")


class AsinOffersTool(_AsinTool):
    """Read the sellers' offers for an Amazon product through Asin."""

    name: str = "Get Amazon offers with Asin"
    description: str = "Get the offers for an Amazon product with Asin: Amazon's own price, the lowest new and used prices, and each seller's price, cheapest first. Input is the ASIN."
    args_schema: type[BaseModel] = AsinOffersToolSchema
    marketplace: str = "com"
    """Amazon store, such as com, co.uk, de or fr."""
    live: bool = False
    """Read the offers live from Amazon (1 credit; a read from the last 3 hours is returned for free). Off: the offers Asin last read, free."""

    def _request(self, asin: str) -> tuple[str, str, dict[str, Any] | None, dict[str, Any] | None]:
        body = {"asin": _client.required(asin, "asin"), "marketplace": self.marketplace}
        return ("POST", "/offers", None, body) if self.live else ("GET", "/offers", body, None)

    def _run(self, asin: str, **kwargs: Any) -> str:
        try:
            return self._text(self._output(self._send(*self._request(asin))))
        except _client.AsinError as exc:
            return str(exc)
