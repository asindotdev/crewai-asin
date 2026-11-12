# crewai-asin

[CrewAI](https://www.crewai.com) tools for [Asin](https://www.asin.dev): search Amazon, read a product's price history and compare its sellers' offers.

## Installation

```bash
pip install crewai-asin
export ASIN_API_KEY="your-api-key"
```

Get an API key at [www.asin.dev/app](https://www.asin.dev/app).

## Tools

| Tool | What it does |
| --- | --- |
| `AsinAmazonSearchTool` | Search an Amazon store through Asin. |
| `AsinPriceHistoryTool` | Read the price history of an Amazon product through Asin. |
| `AsinOffersTool` | Read the sellers' offers for an Amazon product through Asin. |

Each tool takes `api_key` (defaults to `ASIN_API_KEY`), `base_url` and `timeout`, plus the settings shown in its docstring. Errors (invalid key, no credits, rate limit, timeout) come back to the agent as text, without the API key.

```python
from crewai import Agent
from crewai_asin import AsinAmazonSearchTool, AsinPriceHistoryTool

agent = Agent(
    role="Analyst",
    goal="Answer with data from Asin",
    backstory="You use Asin to search Amazon.",
    tools=[AsinAmazonSearchTool(), AsinPriceHistoryTool()],
)

print(AsinAmazonSearchTool().run(**{"query": "kindle"}))
```

## Development

```bash
pip install -e ".[test]"
pytest
```

## License

MIT
